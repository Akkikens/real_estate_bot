"""
FastAPI backend for HouseMatch.

Serves the Next.js frontend with real data from the SQLite/PostgreSQL database.
Run with: uvicorn api.main:app --reload --port 8000

Endpoints:
  GET  /api/v1/properties          — paginated property feed with filters
  GET  /api/v1/properties/{id}     — single property with full score breakdown
  GET  /api/v1/properties/{id}/underwrite — run underwriting on a property
  GET  /api/v1/stats               — dashboard statistics
  GET  /api/v1/watchlist           — current user's watchlist
  POST /api/v1/watchlist/{id}      — add to watchlist
  DELETE /api/v1/watchlist/{id}    — remove from watchlist
  GET  /api/v1/price-drops         — recent price reductions
  GET  /api/v1/health              — health check
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.logging import setup_logging

setup_logging("api.log")

logger = logging.getLogger(__name__)

# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    from database.db import init_db
    init_db()
    logger.info("HouseMatch API started")
    yield

# ── App setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="HouseMatch API",
    description="AI-powered property intelligence for house-hackers and investors.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js dev server and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────────────────────

from api.routes.auth import router as auth_router
from api.routes.watchlist import router as watchlist_router
from api.routes.markets import router as markets_router

app.include_router(auth_router)
app.include_router(watchlist_router)
app.include_router(markets_router)


# ── DB dependency ─────────────────────────────────────────────────────────────

def get_db():
    """Yield a SQLAlchemy session for each request."""
    from database.db import get_session_factory, init_db

    init_db()
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class PropertySummary(BaseModel):
    id: str
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    price: Optional[float] = Field(None, alias="list_price")
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[str] = None
    bart_distance: Optional[float] = Field(None, alias="bart_distance_miles")
    score: Optional[float] = Field(None, alias="total_score")
    rating: Optional[str] = None
    tags: list[str] = []
    listing_url: Optional[str] = None
    source: Optional[str] = None
    listing_type: Optional[str] = None
    first_seen_at: Optional[datetime] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class PropertyDetail(PropertySummary):
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    days_on_market: Optional[int] = None
    hoa_monthly: Optional[float] = None
    listing_remarks: Optional[str] = None
    score_explanation: Optional[str] = None
    score_breakdown: Optional[dict] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    original_price: Optional[float] = None
    estimated_rent_monthly: Optional[float] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_email: Optional[str] = None
    brokerage: Optional[str] = None
    has_adu_signal: Optional[bool] = None
    has_deal_signal: Optional[bool] = None
    has_risk_signal: Optional[bool] = None
    is_watched: Optional[bool] = None
    walk_score: Optional[int] = None
    transit_score: Optional[int] = None
    school_rating: Optional[float] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class UnderwritingResponse(BaseModel):
    address: str
    list_price: float
    down_payment: float
    loan_amount: float
    ltv_pct: float
    interest_rate: float
    monthly_pi: float
    monthly_tax: float
    monthly_insurance: float
    monthly_pmi: float
    monthly_hoa: float
    monthly_total_piti: float
    owner_occupant_burn: float
    house_hack_net: float
    full_rental_net: float
    room_rental_net_low: float
    room_rental_net_mid: float
    room_rental_net_high: float
    cash_to_close: float
    appreciation_conservative: float
    appreciation_moderate: float
    appreciation_optimistic: float
    good_first_property: bool
    verdict: str
    checks: list[str]


class PriceDrop(BaseModel):
    property_id: str
    address: str
    city: Optional[str] = None
    old_price: float
    new_price: float
    drop_pct: float
    drop_date: Optional[datetime] = None
    score: Optional[float] = None


class StatsResponse(BaseModel):
    total_active: int
    total_scored: int
    avg_score: Optional[float] = None
    excellent_count: int
    good_count: int
    price_drops_7d: int
    adu_candidates: int
    newest_listing: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: list[PropertySummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prop_tags(prop) -> list[str]:
    """Build tag list from property signals."""
    tags = []
    if prop.has_adu_signal:
        tags.append("ADU Potential")
    if prop.has_deal_signal:
        tags.append("Deal Signal")
    if prop.has_risk_signal:
        tags.append("⚠ Risk")
    if (prop.beds or 0) >= 4:
        tags.append("House Hack")
    if prop.bart_distance_miles is not None and prop.bart_distance_miles <= 1.0:
        tags.append("Near BART")
    if (prop.lot_size_sqft or 0) >= 6000:
        tags.append("Large Lot")
    if prop.listing_type == "rental":
        tags.append("Rental")
    rating = prop.rating
    if rating == "excellent":
        tags.append("⭐ Excellent")
    return tags


def _to_summary(prop) -> dict:
    """Convert a Property ORM object to a PropertySummary-compatible dict."""
    return {
        "id": prop.id,
        "address": prop.address,
        "city": prop.city,
        "state": prop.state,
        "zip_code": prop.zip_code,
        "list_price": prop.list_price,
        "beds": prop.beds,
        "baths": prop.baths,
        "sqft": prop.sqft,
        "lot_size": f"{prop.lot_size_sqft:,} sqft" if prop.lot_size_sqft else None,
        "bart_distance_miles": prop.bart_distance_miles,
        "total_score": prop.total_score,
        "rating": prop.rating,
        "tags": _prop_tags(prop),
        "listing_url": prop.listing_url,
        "source": prop.source,
        "listing_type": prop.listing_type,
        "first_seen_at": prop.first_seen_at,
    }


def _to_detail(prop) -> dict:
    """Convert a Property ORM to a PropertyDetail-compatible dict."""
    d = _to_summary(prop)
    breakdown = None
    if prop.score_breakdown:
        try:
            breakdown = json.loads(prop.score_breakdown)
        except (json.JSONDecodeError, TypeError):
            pass
    d.update({
        "year_built": prop.year_built,
        "property_type": prop.property_type,
        "days_on_market": prop.days_on_market,
        "hoa_monthly": prop.hoa_monthly,
        "listing_remarks": prop.listing_remarks,
        "score_explanation": prop.score_explanation,
        "score_breakdown": breakdown,
        "latitude": prop.latitude,
        "longitude": prop.longitude,
        "original_price": prop.original_price,
        "estimated_rent_monthly": prop.estimated_rent_monthly,
        "agent_name": prop.agent_name,
        "agent_phone": prop.agent_phone,
        "agent_email": prop.agent_email,
        "brokerage": prop.brokerage,
        "has_adu_signal": prop.has_adu_signal,
        "has_deal_signal": prop.has_deal_signal,
        "has_risk_signal": prop.has_risk_signal,
        "is_watched": prop.is_watched,
        "walk_score": prop.walk_score,
        "transit_score": prop.transit_score,
        "school_rating": prop.school_rating,
    })
    return d


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "housematch-api"}


@app.get("/api/v1/properties", response_model=PaginatedResponse)
def list_properties(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query("score", pattern="^(score|price|newest|bart)$"),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_price: Optional[float] = Query(None, ge=0),
    min_beds: Optional[int] = Query(None, ge=0),
    city: Optional[str] = None,
    listing_type: Optional[str] = Query(None, pattern="^(sale|rental)$"),
    adu_only: bool = False,
    tag: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    from database.models import Property

    query = db.query(Property).filter(
        Property.status == "active",
        Property.is_archived.is_(False),
    )

    if listing_type:
        query = query.filter(Property.listing_type == listing_type)
    if min_score is not None:
        query = query.filter(Property.total_score >= min_score)
    if max_price is not None:
        query = query.filter(Property.list_price <= max_price)
    if min_beds is not None:
        query = query.filter(Property.beds >= min_beds)
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if adu_only:
        query = query.filter(Property.has_adu_signal.is_(True))
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            Property.address.ilike(pattern) | Property.city.ilike(pattern)
        )

    # Sorting
    if sort == "score":
        query = query.order_by(Property.total_score.desc().nullslast())
    elif sort == "price":
        query = query.order_by(Property.list_price.asc().nullslast())
    elif sort == "newest":
        query = query.order_by(Property.first_seen_at.desc().nullslast())
    elif sort == "bart":
        query = query.order_by(Property.bart_distance_miles.asc().nullslast())

    total = query.count()
    offset = (page - 1) * page_size
    props = query.offset(offset).limit(page_size).all()

    return PaginatedResponse(
        items=[PropertySummary(**_to_summary(p)) for p in props],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@app.get("/api/v1/properties/{prop_id}", response_model=PropertyDetail)
def get_property(prop_id: str, db: Session = Depends(get_db)):
    from database.models import Property

    prop = db.query(Property).filter(Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return PropertyDetail(**_to_detail(prop))


@app.get("/api/v1/properties/{prop_id}/underwrite", response_model=UnderwritingResponse)
def underwrite_property(
    prop_id: str,
    down_payment: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    from database.models import Property
    from underwriting.calculator import underwrite

    prop = db.query(Property).filter(Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not prop.list_price:
        raise HTTPException(status_code=400, detail="Property has no list price")

    result = underwrite(prop, down_payment=down_payment)

    # Parse verdict + checks from result
    return UnderwritingResponse(
        address=result.address,
        list_price=result.list_price,
        down_payment=result.down_payment,
        loan_amount=result.loan_amount,
        ltv_pct=result.ltv_pct,
        interest_rate=result.interest_rate,
        monthly_pi=result.monthly.monthly_pi,
        monthly_tax=result.monthly.monthly_tax,
        monthly_insurance=result.monthly.monthly_insurance,
        monthly_pmi=result.monthly.monthly_pmi,
        monthly_hoa=result.monthly.monthly_hoa,
        monthly_total_piti=result.monthly.monthly_total_piti,
        owner_occupant_burn=result.monthly.owner_occupant_burn,
        house_hack_net=result.monthly.house_hack_net,
        full_rental_net=result.monthly.full_rental_net,
        room_rental_net_low=result.monthly.room_rental_net_low,
        room_rental_net_mid=result.monthly.room_rental_net_mid,
        room_rental_net_high=result.monthly.room_rental_net_high,
        cash_to_close=result.cash_to_close.total,
        appreciation_conservative=result.appreciation_conservative.equity_gained,
        appreciation_moderate=result.appreciation_moderate.equity_gained,
        appreciation_optimistic=result.appreciation_optimistic.equity_gained,
        good_first_property=result.good_first_property,
        verdict=result.verdict,
        checks=result.top_considerations,
    )


@app.get("/api/v1/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from database.models import PriceHistory, Property

    active = db.query(Property).filter(
        Property.status == "active",
        Property.is_archived.is_(False),
    )

    total_active = active.count()
    scored = active.filter(Property.total_score.isnot(None))
    total_scored = scored.count()

    avg_score = None
    if total_scored:
        avg_score = round(db.query(func.avg(Property.total_score)).filter(
            Property.status == "active",
            Property.is_archived.is_(False),
            Property.total_score.isnot(None),
        ).scalar() or 0, 1)

    excellent = scored.filter(Property.total_score >= 80).count()
    good = scored.filter(Property.total_score >= 65, Property.total_score < 80).count()

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    drops = db.query(PriceHistory).filter(
        PriceHistory.event == "reduced",
        PriceHistory.recorded_at >= cutoff,
    ).count()

    adu = active.filter(Property.has_adu_signal.is_(True)).count()

    newest = active.order_by(Property.first_seen_at.desc().nullslast()).first()

    return StatsResponse(
        total_active=total_active,
        total_scored=total_scored,
        avg_score=avg_score,
        excellent_count=excellent,
        good_count=good,
        price_drops_7d=drops,
        adu_candidates=adu,
        newest_listing=newest.first_seen_at.isoformat() if newest and newest.first_seen_at else None,
    )


# NOTE: Per-user watchlist endpoints are in api/routes/watchlist.py
# They use JWT auth and the WatchlistItem model for proper multi-tenancy.


@app.get("/api/v1/price-drops", response_model=list[PriceDrop])
def get_price_drops(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    from database.models import PriceHistory, Property

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(PriceHistory, Property)
        .join(Property, PriceHistory.property_id == Property.id)
        .filter(
            PriceHistory.event == "reduced",
            PriceHistory.recorded_at >= cutoff,
        )
        .order_by(PriceHistory.recorded_at.desc())
        .limit(50)
        .all()
    )

    drops = []
    for ph, prop in rows:
        old_p = ph.old_price or 0
        new_p = ph.new_price or prop.list_price or 0
        pct = ((old_p - new_p) / old_p * 100) if old_p > 0 else 0
        drops.append(PriceDrop(
            property_id=prop.id,
            address=prop.address,
            city=prop.city,
            old_price=old_p,
            new_price=new_p,
            drop_pct=round(pct, 1),
            drop_date=ph.recorded_at,
            score=prop.total_score,
        ))
    return drops


# ── Comps endpoint ────────────────────────────────────────────────────────────

class CompResponse(BaseModel):
    property_id: str
    address: str
    city: str
    list_price: float
    beds: int
    baths: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    total_score: Optional[float] = None
    listing_url: Optional[str] = None
    similarity: float
    price_diff_pct: float
    sqft_diff_pct: Optional[float] = None
    distance_miles: Optional[float] = None


@app.get("/api/v1/properties/{prop_id}/comps", response_model=list[CompResponse])
def get_comps(
    prop_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Find comparable properties for a given property."""
    from database.models import Property
    from scoring.comps import find_comps

    prop = db.query(Property).filter(Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    comps = find_comps(db, prop, limit=limit)
    return [CompResponse(
        property_id=c.property_id,
        address=c.address,
        city=c.city,
        list_price=c.list_price,
        beds=c.beds,
        baths=c.baths,
        sqft=c.sqft,
        year_built=c.year_built,
        total_score=c.total_score,
        listing_url=c.listing_url,
        similarity=c.similarity,
        price_diff_pct=c.price_diff_pct,
        sqft_diff_pct=c.sqft_diff_pct,
        distance_miles=c.distance_miles,
    ) for c in comps]


# ── Export endpoints ──────────────────────────────────────────────────────────

@app.get("/api/v1/export/properties.csv")
def export_properties_csv(
    min_score: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    city: Optional[str] = None,
    listing_type: Optional[str] = Query(None, pattern="^(sale|rental)$"),
    db: Session = Depends(get_db),
):
    """Export filtered properties as a CSV download."""
    from fastapi.responses import Response
    from database.models import Property
    from reports.export import properties_to_csv

    query = db.query(Property).filter(
        Property.status == "active",
        Property.is_archived.is_(False),
    )
    if listing_type:
        query = query.filter(Property.listing_type == listing_type)
    if min_score is not None:
        query = query.filter(Property.total_score >= min_score)
    if max_price is not None:
        query = query.filter(Property.list_price <= max_price)
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))

    props = query.order_by(Property.total_score.desc().nullslast()).limit(500).all()
    csv_content = properties_to_csv(props)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=housematch_properties.csv"},
    )


@app.get("/api/v1/properties/{prop_id}/underwrite.csv")
def export_underwriting_csv(
    prop_id: str,
    down_payment: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """Export underwriting report as CSV."""
    from fastapi.responses import Response
    from database.models import Property
    from underwriting.calculator import underwrite
    from reports.export import underwriting_to_csv

    prop = db.query(Property).filter(Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not prop.list_price:
        raise HTTPException(status_code=400, detail="Property has no list price")

    result = underwrite(prop, down_payment=down_payment)
    csv_content = underwriting_to_csv(result)
    safe_addr = (prop.address or "property").replace(" ", "_")[:30]

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=underwriting_{safe_addr}.csv"},
    )


@app.get("/api/v1/properties/{prop_id}/underwrite.html")
def export_underwriting_html(
    prop_id: str,
    down_payment: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    """
    Export underwriting report as a printable HTML page.
    Open in browser and use Ctrl+P / Cmd+P to save as PDF.
    """
    from fastapi.responses import HTMLResponse
    from database.models import Property
    from underwriting.calculator import underwrite
    from reports.export import underwriting_to_html

    prop = db.query(Property).filter(Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not prop.list_price:
        raise HTTPException(status_code=400, detail="Property has no list price")

    result = underwrite(prop, down_payment=down_payment)
    html = underwriting_to_html(result, prop=prop)

    return HTMLResponse(content=html)
