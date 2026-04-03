"""
Rental Scorer
=============
Scores rental listings 0–100 based on Akshay's rental priorities:

  1. Amenities (25%): stainless steel appliances, in-unit washer/dryer, etc.
  2. Safety (25%): neighborhood safety signals
  3. Transit (25%): BART 5-10 min walk, or ferry access to SF
  4. Groceries/Walkability (15%): TJ's, Costco, Safeway walkable
  5. Value (10%): price vs average for the area
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from database.models import Property

logger = logging.getLogger(__name__)

# ── Amenity keywords ─────────────────────────────────────────────────────────

PREMIUM_AMENITIES = {
    "stainless steel": 8,
    "stainless appliance": 8,
    "ss appliance": 6,
    "granite": 4,
    "quartz": 4,
    "marble counter": 4,
}

WASHER_DRYER_KEYWORDS = [
    "in unit washer", "in-unit washer", "in unit w/d", "in-unit w/d",
    "washer dryer in unit", "washer/dryer in unit", "w/d in unit",
    "washer and dryer", "washer/dryer included", "washer dryer included",
    "in unit laundry", "in-unit laundry", "private laundry",
    "own washer", "own w/d",
]

SHARED_LAUNDRY_KEYWORDS = [
    "shared laundry", "on-site laundry", "onsite laundry", "coin laundry",
    "laundry on site", "laundry room", "community laundry",
]

OTHER_AMENITIES = {
    "dishwasher": 3,
    "central air": 3,
    "central a/c": 3,
    "ac included": 2,
    "hardwood": 3,
    "remodeled": 4,
    "renovated": 4,
    "updated kitchen": 4,
    "new kitchen": 4,
    "new appliance": 3,
    "parking": 3,
    "garage": 4,
    "balcony": 2,
    "patio": 2,
    "yard": 2,
    "pet friendly": 2,
    "pets ok": 2,
    "cats ok": 1,
    "dogs ok": 2,
}

# ── Safety keywords ──────────────────────────────────────────────────────────

SAFE_NEIGHBORHOODS = {
    "alameda": 9,
    "rockridge": 9,
    "piedmont": 9,
    "montclair": 9,
    "grand lake": 8,
    "lake merritt": 7,
    "temescal": 8,
    "albany": 8,
    "el cerrito": 8,
    "berkeley hills": 9,
    "north berkeley": 8,
    "claremont": 9,
    "emeryville": 7,
    "adams point": 7,
    "lakeshore": 8,
}

UNSAFE_KEYWORDS = [
    "east oakland", "deep east", "international blvd", "coliseum",
    "hegenberger", "elmhurst", "seminary", "brookfield",
    "98th", "105th", "ghost town",
]

SAFE_KEYWORDS = [
    "safe neighborhood", "quiet street", "quiet neighborhood",
    "low crime", "family friendly", "tree lined", "tree-lined",
    "residential area", "quiet area",
]

# ── Transit: BART stations ───────────────────────────────────────────────────

BART_STATION_KEYWORDS = [
    "bart", "near bart", "walk to bart", "blocks from bart",
    "steps to bart", "close to bart", "minute to bart", "min to bart",
]

BART_CITY_SCORES = {
    "oakland": 8,      # Multiple BART stations
    "berkeley": 8,     # Downtown, Ashby, North Berkeley
    "el cerrito": 8,   # El Cerrito Plaza, El Cerrito del Norte
    "albany": 6,       # Walk to El Cerrito BART
    "emeryville": 6,   # MacArthur BART nearby
    "richmond": 7,     # Richmond BART + ferry
    "alameda": 5,      # No BART but ferry to SF
    "fremont": 7,      # Fremont BART, Warm Springs
}

FERRY_KEYWORDS = [
    "ferry", "near ferry", "walk to ferry", "ferry terminal",
    "harbor bay ferry", "alameda ferry", "oakland ferry",
]

# ── Grocery ──────────────────────────────────────────────────────────────────

GROCERY_KEYWORDS = {
    "trader joe": 5,
    "costco": 4,
    "safeway": 3,
    "whole foods": 4,
    "grocery": 2,
    "market": 1,
    "sprouts": 3,
    "lucky": 2,
    "target": 2,
    "walmart": 2,
}

WALKABLE_GROCERY_CITIES = {
    "alameda": 7,       # Park St has TJ's, Safeway, etc.
    "oakland": 7,       # Grand Lake, Rockridge, Temescal all walkable
    "berkeley": 8,      # TJ's on University, Safeway, WF on Telegraph
    "emeryville": 8,    # Target, TJ's, many options
    "albany": 7,        # Solano Ave shops
    "el cerrito": 6,    # El Cerrito Plaza
    "richmond": 5,      # Hilltop Mall area
}


# ── Scoring functions ────────────────────────────────────────────────────────

def _score_amenities(prop: Property) -> tuple[float, str]:
    """Score amenities: stainless steel, in-unit W/D, dishwasher, etc."""
    remarks = (prop.listing_remarks or "").lower()
    score = 0.0
    found = []

    # Premium kitchen
    for kw, pts in PREMIUM_AMENITIES.items():
        if kw in remarks:
            score += pts
            found.append(kw)
            break  # only count once

    # Washer/dryer
    if any(kw in remarks for kw in WASHER_DRYER_KEYWORDS):
        score += 10
        found.append("in-unit W/D")
    elif any(kw in remarks for kw in SHARED_LAUNDRY_KEYWORDS):
        score += 3
        found.append("shared laundry")

    # Other amenities
    for kw, pts in OTHER_AMENITIES.items():
        if kw in remarks:
            score += pts
            found.append(kw)

    # Normalize to 0-10
    score = min(score / 3.5, 10.0)
    note = f"Amenities: {', '.join(found[:5])}" if found else "No amenity details in listing"
    return round(score, 1), note


def _score_safety(prop: Property) -> tuple[float, str]:
    """Score safety based on neighborhood and keywords."""
    remarks = (prop.listing_remarks or "").lower()
    address = (prop.address or "").lower()
    city = (prop.city or "").lower().strip()
    score = 5.0  # neutral
    notes = []

    # Check known safe neighborhoods
    for hood, safety in SAFE_NEIGHBORHOODS.items():
        if hood in remarks or hood in address or hood == city:
            score = safety
            notes.append(f"{hood.title()} — safety {safety}/10")
            break

    # Check unsafe keywords
    for kw in UNSAFE_KEYWORDS:
        if kw in remarks or kw in address:
            score = max(score - 4, 1.0)
            notes.append(f"Caution: {kw}")
            break

    # Check safe keywords
    for kw in SAFE_KEYWORDS:
        if kw in remarks:
            score = min(score + 1.5, 10.0)
            notes.append(kw)
            break

    # City-level fallback
    if not notes:
        city_safety = {
            "alameda": 8.5, "albany": 8, "berkeley": 7, "el cerrito": 7.5,
            "emeryville": 6.5, "oakland": 5.5, "richmond": 5, "fremont": 7.5,
        }
        s = city_safety.get(city, 5.0)
        score = s
        notes.append(f"{city.title()} avg safety ~{s}/10")

    return round(min(score, 10.0), 1), " | ".join(notes) if notes else "Safety unknown"


def _score_transit(prop: Property) -> tuple[float, str]:
    """Score BART/ferry access. 5-10 min walk to BART is ideal."""
    remarks = (prop.listing_remarks or "").lower()
    city = (prop.city or "").lower().strip()
    score = 4.0
    notes = []

    # BART mentions in listing
    bart_mentioned = any(kw in remarks for kw in BART_STATION_KEYWORDS)
    if bart_mentioned:
        score = 8.5
        notes.append("BART mentioned in listing")

        # Check for walking distance specifics
        walk_match = re.search(r"(\d+)\s*(?:min|minute|block)", remarks)
        if walk_match:
            mins = int(walk_match.group(1))
            if mins <= 5:
                score = 10.0
                notes.append(f"{mins} min walk to BART — ideal")
            elif mins <= 10:
                score = 9.0
                notes.append(f"{mins} min walk to BART — great")
            elif mins <= 15:
                score = 7.0
                notes.append(f"{mins} min to BART — good")

    # Ferry access (especially Alameda/Oakland)
    ferry_mentioned = any(kw in remarks for kw in FERRY_KEYWORDS)
    if ferry_mentioned:
        score = max(score, 7.5)
        notes.append("Ferry access to SF")

    # City-level BART estimate
    if not bart_mentioned and not ferry_mentioned:
        city_score = BART_CITY_SCORES.get(city, 4.0)
        score = city_score
        notes.append(f"{city.title()} — BART/transit score {city_score}/10")

    # Alameda ferry bonus
    if city == "alameda" and not bart_mentioned:
        score = max(score, 6.5)
        if not ferry_mentioned:
            notes.append("Alameda — ferry to SF available")

    # BART distance from Property model
    if prop.bart_distance_miles is not None:
        d = prop.bart_distance_miles
        if d <= 0.3:
            score = max(score, 10.0)
        elif d <= 0.5:
            score = max(score, 9.0)
        elif d <= 1.0:
            score = max(score, 7.5)

    return round(min(score, 10.0), 1), " | ".join(notes) if notes else "Transit info unavailable"


def _score_groceries(prop: Property) -> tuple[float, str]:
    """Score walkable grocery access."""
    remarks = (prop.listing_remarks or "").lower()
    city = (prop.city or "").lower().strip()
    score = 4.0
    found = []

    for kw, pts in GROCERY_KEYWORDS.items():
        if kw in remarks:
            score += pts
            found.append(kw)

    # City-level walkability to groceries
    city_score = WALKABLE_GROCERY_CITIES.get(city, 4.0)
    score = max(score, city_score)

    score = min(score, 10.0)
    note = f"Grocery: {', '.join(found[:4])}" if found else f"{city.title()} grocery walkability ~{city_score}/10"
    return round(score, 1), note


def _score_value(prop: Property) -> tuple[float, str]:
    """Score price value relative to area averages."""
    price = prop.list_price
    if not price:
        return 5.0, "No price data"

    city = (prop.city or "").lower().strip()
    beds = prop.beds or 1

    # Rough 1BR avg rents by city (2025-2026 estimates)
    avg_rents = {
        "alameda": 1800, "oakland": 1700, "berkeley": 1900,
        "emeryville": 1850, "albany": 1750, "el cerrito": 1600,
        "richmond": 1400, "fremont": 1900,
    }

    avg = avg_rents.get(city, 1700)
    # Adjust for bedrooms
    if beds >= 2:
        avg *= 1.35

    ratio = price / avg if avg > 0 else 1.0

    if ratio <= 0.70:
        return 10.0, f"${price:,.0f} is {(1-ratio)*100:.0f}% below avg — great value"
    elif ratio <= 0.85:
        return 8.0, f"${price:,.0f} is below avg — good value"
    elif ratio <= 1.0:
        return 6.0, f"${price:,.0f} is around avg — fair"
    elif ratio <= 1.15:
        return 4.0, f"${price:,.0f} is slightly above avg"
    else:
        return 2.0, f"${price:,.0f} is well above avg"


# ── Main scorer ──────────────────────────────────────────────────────────────

RENTAL_WEIGHTS = {
    "amenities": 0.25,
    "safety": 0.25,
    "transit": 0.25,
    "groceries": 0.15,
    "value": 0.10,
}


def score_rental(prop: Property) -> dict[str, Any]:
    """Score a rental property 0-100. Updates prop in place."""
    dimensions = {
        "amenities": _score_amenities(prop),
        "safety": _score_safety(prop),
        "transit": _score_transit(prop),
        "groceries": _score_groceries(prop),
        "value": _score_value(prop),
    }

    total = sum(
        score * RENTAL_WEIGHTS[dim] * 10
        for dim, (score, _) in dimensions.items()
    )
    total = max(0.0, min(100.0, total))

    # Rating
    if total >= 75:
        rating = "excellent"
    elif total >= 60:
        rating = "good"
    elif total >= 45:
        rating = "watch"
    else:
        rating = "skip"

    # Build explanation
    lines = [f"Rental Score: {total:.0f}/100 ({rating.upper()})"]
    for dim, (score, note) in sorted(dimensions.items(), key=lambda x: x[1][0], reverse=True):
        weight_pct = int(RENTAL_WEIGHTS[dim] * 100)
        lines.append(f"  {dim.title()} ({weight_pct}%): {score:.1f}/10 — {note}")

    explanation = "\n".join(lines)

    # Update property
    prop.total_score = round(total, 1)
    prop.score_explanation = explanation
    prop.score_breakdown = json.dumps({
        dim: {"score": round(score, 2), "weight": RENTAL_WEIGHTS[dim], "note": note}
        for dim, (score, note) in dimensions.items()
    })
    prop.rating = rating

    return {"total_score": round(total, 1), "rating": rating, "explanation": explanation}


def score_rental_and_update(prop: Property) -> float:
    """Score a rental and return total score."""
    result = score_rental(prop)
    return result["total_score"]
