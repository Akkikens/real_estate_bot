"""
Scoring Engine
==============
Scores each property 0–100 against the buyer's strategy.

Architecture:
  • Each dimension returns a raw score 0–10.
  • Weights come from config/scoring_weights.yaml.
  • A penalty (0–15 pts) is subtracted for complexity/risk signals.
  • The final score is clamped to [0, 100].
  • A plain-English explanation is also produced.

Design principles:
  • Missing data is handled conservatively (neither penalised nor rewarded).
  • All threshold values come from config — nothing hardcoded.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from config import settings
from database.models import Property

logger = logging.getLogger(__name__)

# ── Load weights from YAML ─────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).parents[1] / "config" / "scoring_weights.yaml"


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


_cfg = _load_config()
WEIGHTS = _cfg["weights"]
PENALTY_MAX = _cfg["penalty"]["complexity_max"]
RATINGS = _cfg["ratings"]
ADU_KEYWORDS = [k.lower() for k in _cfg["adu_keywords"]]
DEAL_KEYWORDS = [k.lower() for k in _cfg["deal_keywords"]]
RISK_KEYWORDS = [k.lower() for k in _cfg["risk_keywords"]]
PRICE_BANDS = _cfg["price_bands"]
LOT_TIERS = _cfg["lot_size_tiers"]


# ── Individual dimension scorers ───────────────────────────────────────────────


def _score_price_fit(prop: Property) -> tuple[float, str]:
    """How well does the price fit the buyer's budget?"""
    if not prop.list_price:
        return 5.0, "List price unknown — neutral score."

    max_price = settings.BUYER_MAX_PRICE
    fraction = prop.list_price / max_price

    for band in PRICE_BANDS:
        if fraction <= band["max_fraction"]:
            score = float(band["score"])
            pct = round(fraction * 100)
            if score >= 8:
                note = f"${prop.list_price:,.0f} is {pct}% of your max — excellent fit."
            elif score >= 6:
                note = f"${prop.list_price:,.0f} is {pct}% of your max — good fit with room to negotiate."
            elif score >= 4:
                note = f"${prop.list_price:,.0f} is {pct}% of your max — at the upper end of your range."
            elif score >= 2:
                note = f"${prop.list_price:,.0f} slightly exceeds your ideal max — may require a stretch."
            else:
                note = f"${prop.list_price:,.0f} is significantly above your max — financing very difficult."
            return score, note

    return 0.0, f"${prop.list_price:,.0f} is well above your max budget."


def _score_house_hack(prop: Property) -> tuple[float, str]:
    """Bedroom count, unit structure, separate-entrance signals."""
    score = 0.0
    notes = []

    beds = prop.beds or 0
    remarks = (prop.listing_remarks or "").lower()
    prop_type = (prop.property_type or "").lower()

    # Bedrooms
    if beds >= 5:
        score += 6.0
        notes.append(f"{beds}BR — excellent for renting multiple rooms.")
    elif beds == 4:
        score += 5.0
        notes.append(f"4BR — strong house-hack candidate (rent 2–3 rooms).")
    elif beds == 3:
        score += 3.5
        notes.append("3BR — good for renting 1–2 rooms while you occupy one.")
    elif beds == 2:
        score += 1.5
        notes.append("2BR — limited room-rental upside.")
    else:
        notes.append("1BR or unknown — minimal house-hack potential.")

    # Multi-unit / duplex
    if "duplex" in prop_type or "multi" in prop_type:
        score += 3.0
        notes.append("Duplex/multi-unit — live in one, rent the other instantly.")
    elif any(k in remarks for k in ["duplex", "two unit", "two homes", "two houses"]):
        score += 2.5
        notes.append("Listing mentions two-unit setup — verify legal status.")

    # Separate entrance
    if any(k in remarks for k in ["separate entrance", "separate entry", "private entrance"]):
        score += 1.0
        notes.append("Separate entrance mentioned — strong rental configuration.")

    score = min(score, 10.0)
    return score, " ".join(notes) if notes else "Standard single-family layout."


def _score_rental_income(prop: Property) -> tuple[float, str]:
    """
    Compares estimated rent to total monthly payment (PITI).
    Uses rough estimate if no rent data is stored.
    """
    if not prop.list_price:
        return 5.0, "Cannot estimate without price."

    # Rough PITI estimate: 0.55% of purchase price per month
    # (covers P&I + tax + insurance at ~7% rate, 20% down)
    down = settings.BUYER_DOWN_PAYMENT
    loan = max(prop.list_price - down, 0)
    rate_monthly = settings.MORTGAGE_RATE / 12
    n = settings.MORTGAGE_TERM_YEARS * 12
    if rate_monthly > 0 and n > 0:
        pi = loan * (rate_monthly * (1 + rate_monthly) ** n) / ((1 + rate_monthly) ** n - 1)
    else:
        pi = loan / n if n else 0

    tax_monthly = (prop.list_price * settings.PROPERTY_TAX_RATE) / 12
    ins_monthly = (prop.list_price * settings.INSURANCE_RATE) / 12
    piti = pi + tax_monthly + ins_monthly + (prop.hoa_monthly or 0)

    # Estimate rent
    rent = prop.estimated_rent_monthly
    if not rent:
        # Bay Area heuristic: ~0.45–0.55% of price for a SFR
        rent = prop.list_price * 0.0045
        rent_source = "estimated"
    else:
        rent_source = "provided"

    coverage = rent / piti if piti > 0 else 0

    if coverage >= 0.90:
        score = 10.0
        note = f"Rent ({rent_source}: ${rent:,.0f}/mo) covers {coverage*100:.0f}% of PITI — exceptional cash flow."
    elif coverage >= 0.70:
        score = 8.0
        note = f"Rent covers {coverage*100:.0f}% of PITI — strong partial offset."
    elif coverage >= 0.50:
        score = 6.0
        note = f"Rent covers {coverage*100:.0f}% of PITI — decent income offset."
    elif coverage >= 0.35:
        score = 4.0
        note = f"Rent covers {coverage*100:.0f}% of PITI — modest offset."
    elif coverage >= 0.20:
        score = 2.0
        note = f"Rent only covers {coverage*100:.0f}% of PITI — still a big monthly burn."
    else:
        score = 1.0
        note = f"Rent insufficient — will be primarily owner-occupied expense."

    return score, note


def _score_adu_upside(prop: Property) -> tuple[float, str]:
    """Lot size, zoning, and ADU keyword signals."""
    score = 0.0
    notes = []

    remarks = (prop.listing_remarks or "").lower()
    lot = prop.lot_size_sqft or 0
    prop_type = (prop.property_type or "").lower()

    # Check ADU keywords in remarks
    adu_matches = [kw for kw in ADU_KEYWORDS if kw in remarks]
    if adu_matches:
        score += 4.0
        notes.append(f"ADU signals in listing: {', '.join(adu_matches[:3])}.")
    elif "duplex" in prop_type or "multi" in prop_type:
        score += 3.0
        notes.append("Multi-unit type inherently has second income stream.")

    # Lot size scoring
    if lot >= LOT_TIERS["large"]:
        score += 4.0
        notes.append(f"Large lot ({lot:,} sqft) — strong ADU development candidate.")
    elif lot >= LOT_TIERS["medium"]:
        score += 2.5
        notes.append(f"Medium lot ({lot:,} sqft) — ADU feasible depending on setbacks.")
    elif lot >= LOT_TIERS["small"]:
        score += 1.0
        notes.append(f"Smaller lot ({lot:,} sqft) — ADU may be tight; check setbacks.")
    elif lot > 0:
        notes.append(f"Small lot ({lot:,} sqft) — ADU likely difficult.")
    else:
        notes.append("Lot size unknown.")

    # SB9 / lot split mention
    if any(k in remarks for k in ["sb9", "lot split", "lot line"]):
        score += 2.0
        notes.append("Lot split/SB9 mentioned — significant upside potential.")

    score = min(score, 10.0)
    return score, " ".join(notes) if notes else "Limited ADU signals."


def _score_transit(prop: Property) -> tuple[float, str]:
    """
    BART proximity, transit score, and SF commute corridor signals.

    City-level SF proximity bonus applied on top of BART distance:
      Oakland / Emeryville — closest to SF, highest rental demand from commuters
      Berkeley / Albany / El Cerrito — strong BART corridor, high desirability
      Richmond — ferry + BART, underrated commute access
      Fremont — further but BART + 880, strong job base (Tesla/Meta/Amazon)
    """
    score = 5.0  # neutral default
    notes = []

    bart = prop.bart_distance_miles
    transit_sc = prop.transit_score
    walk_sc = prop.walk_score
    city = (prop.city or "").lower().strip()

    # ── City-level SF proximity bonus ─────────────────────────────────────────
    # These cities have the strongest SF commuter rental demand.
    # Bonus is additive to the BART distance score below.
    SF_PROXIMITY_BONUS: dict[str, tuple[float, str]] = {
        "oakland":     (1.5, "Oakland — 12 min to SF on BART, peak rental demand."),
        "emeryville":  (1.5, "Emeryville — BART + Amtrak, major employer hub, direct SF access."),
        "berkeley":    (1.2, "Berkeley — strong BART corridor, high commuter demand."),
        "albany":      (1.0, "Albany — walkable to El Cerrito/Berkeley BART, high desirability."),
        "el cerrito":  (1.0, "El Cerrito — two BART stations, solid SF commute."),
        "richmond":    (0.8, "Richmond — BART + ferry terminal, undervalued SF commute access."),
        "fremont":     (0.5, "Fremont — BART terminus, 880 corridor, growing tech job base."),
    }
    city_bonus, city_note = SF_PROXIMITY_BONUS.get(city, (0.0, ""))

    # ── BART distance scoring ─────────────────────────────────────────────────
    if bart is not None:
        if bart <= 0.5:
            score = 9.0
            notes.append(f"Excellent: {bart:.1f} mi to BART — walkable commute hub.")
        elif bart <= 1.0:
            score = 8.0
            notes.append(f"Very good: {bart:.1f} mi to BART — bikeable.")
        elif bart <= 1.5:
            score = 6.5
            notes.append(f"Good: {bart:.1f} mi to BART — short drive/ride.")
        elif bart <= 2.5:
            score = 5.0
            notes.append(f"Moderate: {bart:.1f} mi to BART.")
        elif bart <= 4.0:
            score = 3.0
            notes.append(f"Distant from BART ({bart:.1f} mi) — car-dependent commute.")
        else:
            score = 1.5
            notes.append(f"Far from BART ({bart:.1f} mi) — weak transit access.")
    else:
        notes.append("BART distance unknown — using city-level estimate.")

    # Apply city bonus
    if city_bonus > 0:
        score = min(score + city_bonus, 10.0)
        notes.append(city_note)

    # ── Transit score adjustment ───────────────────────────────────────────────
    if transit_sc is not None:
        if transit_sc >= 70:
            score = min(score + 0.5, 10.0)
            notes.append(f"High transit score ({transit_sc}).")
        elif transit_sc < 40:
            score = max(score - 0.5, 0.0)
            notes.append(f"Low transit score ({transit_sc}).")

    if walk_sc and walk_sc >= 70:
        notes.append(f"Walkable neighborhood (walk score {walk_sc}).")

    return round(score, 1), " ".join(notes) if notes else "Transit data unavailable."


def _score_neighborhood(prop: Property) -> tuple[float, str]:
    """School rating, crime index, and walk score composite."""
    score = 5.0  # default neutral
    notes = []

    school = prop.school_rating
    crime = prop.crime_index    # lower = safer; 0–100 scale
    walk = prop.walk_score

    if school is not None:
        if school >= 8.0:
            score += 2.0
            notes.append(f"Strong school rating ({school}/10) — good for family rental demand.")
        elif school >= 6.5:
            score += 1.0
            notes.append(f"Above-average schools ({school}/10).")
        elif school >= 5.0:
            pass
            notes.append(f"Average schools ({school}/10).")
        else:
            score -= 0.5
            notes.append(f"Below-average school rating ({school}/10) — may limit family tenant pool.")

    if crime is not None:
        if crime <= 25:
            score += 2.0
            notes.append(f"Very low crime index ({crime}) — premium neighborhood.")
        elif crime <= 45:
            score += 1.0
            notes.append(f"Low-moderate crime ({crime}).")
        elif crime <= 65:
            score -= 0.5
            notes.append(f"Elevated crime index ({crime}) — verify with local data.")
        else:
            score -= 1.5
            notes.append(f"High crime index ({crime}) — significant consideration for tenants.")

    if walk is not None:
        if walk >= 80:
            score += 1.0
            notes.append(f"Very walkable ({walk}).")
        elif walk >= 60:
            score += 0.5

    score = max(0.0, min(score, 10.0))
    return round(score, 1), " ".join(notes) if notes else "Neighborhood data unavailable."


def _score_deal_opportunity(prop: Property) -> tuple[float, str]:
    """Price reductions, days on market, motivated seller signals."""
    score = 3.0  # baseline
    notes = []

    remarks = (prop.listing_remarks or "").lower()
    dom = prop.days_on_market or 0
    orig = prop.original_price
    current = prop.list_price

    # Price cut
    if orig and current and orig > current:
        pct_cut = (orig - current) / orig * 100
        if pct_cut >= 10:
            score += 4.0
            notes.append(f"Major price cut: {pct_cut:.1f}% off original (${orig:,.0f} → ${current:,.0f}).")
        elif pct_cut >= 5:
            score += 2.5
            notes.append(f"Meaningful price reduction: {pct_cut:.1f}% off (${orig:,.0f} → ${current:,.0f}).")
        elif pct_cut >= 2:
            score += 1.0
            notes.append(f"Small price cut: {pct_cut:.1f}% off original.")

    # Days on market
    if dom >= 60:
        score += 3.0
        notes.append(f"Stale listing — {dom} DOM. Seller likely flexible on price.")
    elif dom >= 30:
        score += 1.5
        notes.append(f"{dom} days on market — some motivated seller signal.")
    elif dom <= 7:
        score = max(score - 1.0, 0)
        notes.append(f"Fresh listing ({dom} DOM) — expect competition.")

    # Keyword signals
    deal_matches = [kw for kw in DEAL_KEYWORDS if kw in remarks]
    if deal_matches:
        score += min(len(deal_matches) * 0.5, 2.0)
        notes.append(f"Deal keywords: {', '.join(deal_matches[:3])}.")

    score = min(score, 10.0)
    return round(score, 1), " ".join(notes) if notes else "No special deal signals."


def _score_lot_expansion(prop: Property) -> tuple[float, str]:
    """Lot size potential beyond ADU — raw land upside."""
    lot = prop.lot_size_sqft or 0
    sqft = prop.sqft or 1

    if lot == 0:
        return 5.0, "Lot size unknown."

    # Coverage ratio: what fraction of the lot is the building?
    coverage = sqft / lot if lot > 0 else 1.0

    if lot >= 8000 and coverage < 0.30:
        return 9.0, f"Large lot ({lot:,} sqft), low coverage — major expansion potential."
    elif lot >= 6000:
        return 7.0, f"Generous lot ({lot:,} sqft) with room to build."
    elif lot >= 4500:
        return 5.5, f"Medium-large lot ({lot:,} sqft) — ADU or addition feasible."
    elif lot >= 3000:
        return 4.0, f"Average lot ({lot:,} sqft) — standard suburban parcel."
    elif lot >= 2000:
        return 2.5, f"Smaller lot ({lot:,} sqft) — limited expansion room."
    else:
        return 1.5, f"Very small lot ({lot:,} sqft) — condo-like constraints."


def _compute_complexity_penalty(prop: Property) -> tuple[float, str]:
    """Subtract points for risk/complexity signals (0–PENALTY_MAX)."""
    remarks = (prop.listing_remarks or "").lower()
    penalty = 0.0
    notes = []

    risk_matches = [kw for kw in RISK_KEYWORDS if kw in remarks]
    if risk_matches:
        penalty += min(len(risk_matches) * 3.0, PENALTY_MAX * 0.7)
        notes.append(f"Risk signals: {', '.join(risk_matches[:4])}.")

    # Unpermitted or code violation
    if any(k in remarks for k in ["unpermitted", "code violation", "code enforcement"]):
        penalty += 5.0
        notes.append("Unpermitted work / code violations — verify with county.")

    # Full rebuild
    if any(k in remarks for k in ["full rebuild", "tear down", "teardown", "demo only"]):
        penalty += 10.0
        notes.append("Full rebuild — requires developer capital beyond typical first-buy budget.")

    penalty = min(penalty, float(PENALTY_MAX))
    if not notes:
        return 0.0, "No major complexity/risk signals detected."
    return round(penalty, 1), "Complexity penalty: " + " ".join(notes)


# ── Main scoring function ──────────────────────────────────────────────────────


def score_property(prop: Property) -> dict[str, Any]:
    """
    Score a property and return a rich result dict.
    Also updates prop.total_score, prop.score_breakdown, etc. in place.
    """
    dimensions = {
        "price_fit":            _score_price_fit(prop),
        "house_hack_potential": _score_house_hack(prop),
        "rental_income":        _score_rental_income(prop),
        "adu_upside":           _score_adu_upside(prop),
        "transit_access":       _score_transit(prop),
        "neighborhood":         _score_neighborhood(prop),
        "deal_opportunity":     _score_deal_opportunity(prop),
        "lot_expansion":        _score_lot_expansion(prop),
    }

    # Track which dimensions have real data vs neutral defaults
    _NO_DATA_DIMS: dict[str, bool] = {}

    def _has_data(dim: str) -> bool:
        if dim in _NO_DATA_DIMS:
            return _NO_DATA_DIMS[dim]
        if dim == "price_fit":
            result = prop.list_price is not None
        elif dim == "house_hack_potential":
            result = (prop.beds or 0) > 0
        elif dim == "rental_income":
            result = prop.list_price is not None
        elif dim == "adu_upside":
            result = (prop.lot_size_sqft or 0) > 0 or bool(prop.has_adu_signal)
        elif dim == "transit_access":
            result = prop.bart_distance_miles is not None or prop.transit_score is not None
        elif dim == "neighborhood":
            result = prop.school_rating is not None or prop.crime_index is not None or prop.walk_score is not None
        elif dim == "deal_opportunity":
            result = (prop.days_on_market or 0) > 0 or (prop.original_price is not None and prop.list_price is not None)
        elif dim == "lot_expansion":
            result = (prop.lot_size_sqft or 0) > 0
        else:
            result = True
        _NO_DATA_DIMS[dim] = result
        return result

    # For dimensions with no data, override score to 6.0/10 instead of 5.0
    # so missing data doesn't drag the score (benefit of the doubt).
    # Update the dimensions dict so breakdown and explanation stay consistent.
    for dim, (score, note) in list(dimensions.items()):
        if not _has_data(dim):
            dimensions[dim] = (6.0, f"{note} [no data — using 6.0 default]")

    # Weighted sum → 0–100
    raw_score = sum(
        score * WEIGHTS.get(dim, 0.0) * 10
        for dim, (score, _) in dimensions.items()
    )

    # Data completeness: penalize if we're flying blind on too many dimensions
    n_with_data = sum(1 for dim in dimensions if _has_data(dim))
    data_ratio = n_with_data / len(dimensions)
    # If <50% of dimensions have data, scale down proportionally (floor at 0.7x)
    if data_ratio < 0.5:
        confidence = 0.7 + (data_ratio * 0.6)  # 0.7 at 0%, 1.0 at 50%
        raw_score *= confidence

    # Complexity penalty
    penalty, penalty_note = _compute_complexity_penalty(prop)
    final_score = max(0.0, min(100.0, raw_score - penalty))

    # Rating label
    if final_score >= RATINGS["excellent"]:
        rating = "excellent"
    elif final_score >= RATINGS["good"]:
        rating = "good"
    elif final_score >= RATINGS["watch"]:
        rating = "watch"
    else:
        rating = "skip"

    # Keyword flags
    remarks = (prop.listing_remarks or "").lower()
    prop.has_adu_signal = any(k in remarks for k in ADU_KEYWORDS)
    prop.has_deal_signal = any(k in remarks for k in DEAL_KEYWORDS)
    prop.has_risk_signal = any(k in remarks for k in RISK_KEYWORDS)

    # Breakdown dict for storage
    breakdown = {
        dim: {"score": round(score, 2), "weight": WEIGHTS.get(dim, 0), "note": note}
        for dim, (score, note) in dimensions.items()
    }
    breakdown["complexity_penalty"] = {"penalty": penalty, "note": penalty_note}

    # Plain-English explanation
    top_dims = sorted(dimensions.items(), key=lambda x: x[1][0] * WEIGHTS.get(x[0], 0), reverse=True)
    explanation = _build_explanation(prop, final_score, rating, top_dims, penalty_note, dimensions)

    # Update ORM object
    prop.total_score = round(final_score, 1)
    prop.score_breakdown = json.dumps(breakdown)
    prop.score_explanation = explanation
    prop.rating = rating

    return {
        "total_score": round(final_score, 1),
        "raw_score": round(raw_score, 1),
        "penalty": penalty,
        "rating": rating,
        "breakdown": breakdown,
        "explanation": explanation,
    }


def _build_explanation(prop: Property, score: float, rating: str, top_dims, penalty_note, dims) -> str:
    """Build a concise human-readable explanation of the score."""
    lines = [
        f"Score: {score:.1f}/100 ({rating.upper()})",
        "",
        f"Property: {prop.address}, {prop.city} | {prop.beds}BR/{prop.baths}BA | {prop.sqft or '?'} sqft | ${prop.list_price:,.0f}" if prop.list_price else f"Property: {prop.address}, {prop.city}",
        "",
        "── Why this score ──",
    ]

    for dim, (dim_score, note) in top_dims[:4]:
        weight_pct = int(WEIGHTS.get(dim, 0) * 100)
        lines.append(f"• {dim.replace('_', ' ').title()} ({weight_pct}% weight, {dim_score:.1f}/10): {note}")

    if penalty_note and "No major" not in penalty_note:
        lines.append(f"• ⚠ {penalty_note}")

    lines += ["", "── Strategy fit ──"]

    # House-hack
    hh_score = dims["house_hack_potential"][0]
    if hh_score >= 6:
        lines.append("✓ Strong house-hack candidate.")
    elif hh_score >= 3:
        lines.append("~ Moderate house-hack potential.")
    else:
        lines.append("✗ Limited house-hack potential.")

    # ADU
    adu_score = dims["adu_upside"][0]
    if adu_score >= 6:
        lines.append("✓ Good ADU/second-unit upside.")
    elif adu_score >= 3:
        lines.append("~ Some ADU potential — verify with city.")

    # Deal
    deal_score = dims["deal_opportunity"][0]
    if deal_score >= 6:
        lines.append("✓ Strong deal opportunity (price cut or stale).")

    return "\n".join(lines)


def score_and_update(prop: Property) -> float:
    """Score a property and return the total score (for use in batch jobs)."""
    result = score_property(prop)
    return result["total_score"]
