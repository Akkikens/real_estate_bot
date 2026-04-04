"""
Markets router — list available markets with metadata.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/markets", tags=["markets"])


class MarketSummary(BaseModel):
    id: str
    display_name: str
    state: str
    timezone: str
    transit_system_name: str
    num_cities: int
    status: str  # available, coming_soon, beta


class MarketDetail(MarketSummary):
    cities: list[str]
    property_tax_rate: float
    closing_cost_pct: float
    rent_price_ratio: float
    room_rental_low: float
    room_rental_mid: float
    room_rental_high: float


@router.get("", response_model=list[MarketSummary])
def list_markets():
    from config.market import MARKETS

    results = []
    for mid, m in MARKETS.items():
        results.append(MarketSummary(
            id=m.id,
            display_name=m.display_name,
            state=m.state,
            timezone=m.timezone,
            transit_system_name=m.transit_system_name,
            num_cities=len(m.redfin_region_ids),
            status="available",
        ))
    return results


@router.get("/{market_id}", response_model=MarketDetail)
def get_market(market_id: str):
    from config.market import MARKETS
    from fastapi import HTTPException

    m = MARKETS.get(market_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Market '{market_id}' not found")

    return MarketDetail(
        id=m.id,
        display_name=m.display_name,
        state=m.state,
        timezone=m.timezone,
        transit_system_name=m.transit_system_name,
        num_cities=len(m.redfin_region_ids),
        status="available",
        cities=sorted(m.redfin_region_ids.keys()),
        property_tax_rate=m.property_tax_rate,
        closing_cost_pct=m.closing_cost_pct,
        rent_price_ratio=m.rent_price_ratio,
        room_rental_low=m.room_rental_low,
        room_rental_mid=m.room_rental_mid,
        room_rental_high=m.room_rental_high,
    )
