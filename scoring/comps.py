"""
Comparable Sales / Rental Comps Module
======================================
Finds comparable properties (comps) for a given target property using
database-local data. No external API calls required.

Comp selection strategy:
  1. Same city + similar bedrooms (±1)
  2. Similar price range (±25%)
  3. Similar square footage (±30%)
  4. Scored and ranked by similarity score

Returns the top N most comparable properties with a similarity score.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from database.models import Property

logger = logging.getLogger(__name__)


@dataclass
class CompResult:
    """A single comparable property with similarity metrics."""

    property_id: str
    address: str
    city: str
    list_price: float
    beds: int
    baths: Optional[float]
    sqft: Optional[int]
    year_built: Optional[int]
    total_score: Optional[float]
    listing_url: Optional[str]
    similarity: float          # 0–100, higher = more similar
    price_diff_pct: float      # % difference from target price
    sqft_diff_pct: Optional[float]
    distance_miles: Optional[float]  # haversine distance if coords available


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in miles between two lat/lon points."""
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(a))


def _similarity_score(
    target: Property,
    comp: Property,
) -> tuple[float, float, Optional[float], Optional[float]]:
    """
    Compute a similarity score (0–100) between target and comp.
    Returns (similarity, price_diff_pct, sqft_diff_pct, distance_miles).
    """
    score = 0.0
    max_score = 0.0

    # Price similarity (40 points max)
    t_price = target.list_price or 0
    c_price = comp.list_price or 0
    price_diff_pct = 0.0
    if t_price > 0 and c_price > 0:
        max_score += 40
        price_diff_pct = abs(c_price - t_price) / t_price * 100
        if price_diff_pct <= 5:
            score += 40
        elif price_diff_pct <= 10:
            score += 32
        elif price_diff_pct <= 15:
            score += 24
        elif price_diff_pct <= 25:
            score += 16
        elif price_diff_pct <= 35:
            score += 8

    # Bedroom match (15 points max)
    t_beds = target.beds or 0
    c_beds = comp.beds or 0
    if t_beds > 0 and c_beds > 0:
        max_score += 15
        bed_diff = abs(t_beds - c_beds)
        if bed_diff == 0:
            score += 15
        elif bed_diff == 1:
            score += 8

    # Sqft similarity (20 points max)
    t_sqft = target.sqft or 0
    c_sqft = comp.sqft or 0
    sqft_diff_pct: Optional[float] = None
    if t_sqft > 0 and c_sqft > 0:
        max_score += 20
        sqft_diff_pct = abs(c_sqft - t_sqft) / t_sqft * 100
        if sqft_diff_pct <= 10:
            score += 20
        elif sqft_diff_pct <= 20:
            score += 14
        elif sqft_diff_pct <= 30:
            score += 8

    # Distance proximity (15 points max)
    distance_miles: Optional[float] = None
    if (
        target.latitude and target.longitude
        and comp.latitude and comp.longitude
    ):
        max_score += 15
        distance_miles = _haversine(
            target.latitude, target.longitude,
            comp.latitude, comp.longitude,
        )
        if distance_miles <= 0.5:
            score += 15
        elif distance_miles <= 1.0:
            score += 12
        elif distance_miles <= 2.0:
            score += 8
        elif distance_miles <= 5.0:
            score += 4

    # Year built similarity (10 points max)
    t_year = target.year_built or 0
    c_year = comp.year_built or 0
    if t_year > 0 and c_year > 0:
        max_score += 10
        year_diff = abs(t_year - c_year)
        if year_diff <= 5:
            score += 10
        elif year_diff <= 10:
            score += 7
        elif year_diff <= 20:
            score += 4

    # Normalize to 0–100
    similarity = (score / max_score * 100) if max_score > 0 else 0.0
    return round(similarity, 1), round(price_diff_pct, 1), sqft_diff_pct, distance_miles


def find_comps(
    db: Session,
    target: Property,
    limit: int = 10,
    listing_type: Optional[str] = None,
) -> list[CompResult]:
    """
    Find comparable properties for the given target.

    Filters:
      - Same listing_type (sale or rental)
      - Active and not archived
      - Excludes the target itself
      - Price within ±40%
      - Bedrooms within ±1

    Returns a list of CompResult sorted by similarity (descending).
    """
    lt = listing_type or target.listing_type or "sale"
    t_price = target.list_price or 0
    t_beds = target.beds or 0

    # Build base query
    query = db.query(Property).filter(
        Property.id != target.id,
        Property.status == "active",
        Property.is_archived.is_(False),
        Property.listing_type == lt,
    )

    # Price range filter
    if t_price > 0:
        query = query.filter(
            Property.list_price >= t_price * 0.60,
            Property.list_price <= t_price * 1.40,
        )

    # Bedroom filter
    if t_beds > 0:
        query = query.filter(
            Property.beds >= max(t_beds - 1, 1),
            Property.beds <= t_beds + 1,
        )

    # Same city preferred, but also include nearby cities
    candidates = query.limit(200).all()

    # Score each candidate
    results: list[CompResult] = []
    for comp in candidates:
        similarity, price_diff_pct, sqft_diff_pct, distance_miles = _similarity_score(target, comp)

        # Only include comps with meaningful similarity
        if similarity < 20:
            continue

        results.append(CompResult(
            property_id=comp.id,
            address=comp.address,
            city=comp.city or "",
            list_price=comp.list_price or 0,
            beds=comp.beds or 0,
            baths=comp.baths,
            sqft=comp.sqft,
            year_built=comp.year_built,
            total_score=comp.total_score,
            listing_url=comp.listing_url,
            similarity=similarity,
            price_diff_pct=price_diff_pct,
            sqft_diff_pct=round(sqft_diff_pct, 1) if sqft_diff_pct is not None else None,
            distance_miles=round(distance_miles, 2) if distance_miles is not None else None,
        ))

    # Sort by similarity descending
    results.sort(key=lambda r: r.similarity, reverse=True)
    return results[:limit]


def comp_summary(target: Property, comps: list[CompResult]) -> str:
    """
    Generate a human-readable comp analysis summary.
    """
    if not comps:
        return "No comparable properties found in the database."

    prices = [c.list_price for c in comps if c.list_price > 0]
    avg_price = sum(prices) / len(prices) if prices else 0
    t_price = target.list_price or 0

    lines = [
        f"Comp Analysis for {target.address}, {target.city}",
        f"Target: ${t_price:,.0f} | {target.beds or '?'}BR | {target.sqft or '?'} sqft",
        f"Found {len(comps)} comparable properties:",
        "",
    ]

    for i, c in enumerate(comps[:5], 1):
        price_dir = "below" if c.list_price < t_price else "above"
        lines.append(
            f"  {i}. {c.address}, {c.city} — ${c.list_price:,.0f} "
            f"({c.price_diff_pct:.0f}% {price_dir}) | "
            f"{c.beds}BR | Similarity: {c.similarity:.0f}%"
        )

    lines.append("")
    if avg_price > 0 and t_price > 0:
        diff = (t_price - avg_price) / avg_price * 100
        if diff < -5:
            lines.append(f"Target is priced {abs(diff):.0f}% BELOW comp average (${avg_price:,.0f}) — potential value.")
        elif diff > 5:
            lines.append(f"Target is priced {diff:.0f}% ABOVE comp average (${avg_price:,.0f}) — negotiate down.")
        else:
            lines.append(f"Target is priced in line with comp average (${avg_price:,.0f}).")

    return "\n".join(lines)
