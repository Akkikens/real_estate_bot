"""
Watchlist router — per-user saved properties with notes and pipeline stages.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class WatchlistItemResponse(BaseModel):
    id: int
    property_id: str
    saved_at: Optional[datetime] = None
    price_at_save: Optional[float] = None
    notes: Optional[str] = None
    pipeline_stage: str = "watching"
    # Property summary fields
    address: Optional[str] = None
    city: Optional[str] = None
    price: Optional[float] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    bart_distance: Optional[float] = None
    score: Optional[float] = None
    rating: Optional[str] = None
    tags: list[str] = []
    listing_url: Optional[str] = None
    # Price change since save
    price_change: Optional[float] = None
    price_change_pct: Optional[float] = None


class WatchlistAddRequest(BaseModel):
    notes: Optional[str] = None

class WatchlistUpdateNotes(BaseModel):
    notes: Optional[str] = None

class WatchlistUpdateStage(BaseModel):
    pipeline_stage: str  # watching, touring, offer_sent, under_contract, closed, passed


# ── DB dependency ─────────────────────────────────────────────────────────────

def _get_db():
    from database.db import get_session_factory, init_db
    init_db()
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prop_tags(prop) -> list[str]:
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
    return tags


def _to_response(item, prop) -> WatchlistItemResponse:
    price_change = None
    price_change_pct = None
    if item.price_at_save and prop.list_price:
        price_change = prop.list_price - item.price_at_save
        if item.price_at_save > 0:
            price_change_pct = round((price_change / item.price_at_save) * 100, 1)

    return WatchlistItemResponse(
        id=item.id,
        property_id=item.property_id,
        saved_at=item.saved_at,
        price_at_save=item.price_at_save,
        notes=item.notes,
        pipeline_stage=item.pipeline_stage,
        address=prop.address,
        city=prop.city,
        price=prop.list_price,
        beds=prop.beds,
        baths=prop.baths,
        sqft=prop.sqft,
        bart_distance=prop.bart_distance_miles,
        score=prop.total_score,
        rating=prop.rating,
        tags=_prop_tags(prop),
        listing_url=prop.listing_url,
        price_change=price_change,
        price_change_pct=price_change_pct,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[WatchlistItemResponse])
def get_watchlist(
    user=Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    from database.models import Property, WatchlistItem

    items = (
        db.query(WatchlistItem, Property)
        .join(Property, WatchlistItem.property_id == Property.id)
        .filter(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.saved_at.desc())
        .all()
    )
    return [_to_response(item, prop) for item, prop in items]


@router.post("/{property_id}", response_model=WatchlistItemResponse, status_code=201)
def add_to_watchlist(
    property_id: str,
    body: Optional[WatchlistAddRequest] = None,
    user=Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    from database.models import Property, WatchlistItem

    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    existing = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.property_id == property_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Property already in watchlist")

    item = WatchlistItem(
        user_id=user.id,
        property_id=property_id,
        price_at_save=prop.list_price,
        notes=body.notes if body else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return _to_response(item, prop)


@router.delete("/{property_id}")
def remove_from_watchlist(
    property_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    from database.models import WatchlistItem

    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.property_id == property_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Property not in watchlist")

    db.delete(item)
    db.commit()
    return {"status": "removed", "property_id": property_id}


@router.put("/{property_id}/notes", response_model=WatchlistItemResponse)
def update_notes(
    property_id: str,
    body: WatchlistUpdateNotes,
    user=Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    from database.models import Property, WatchlistItem

    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.property_id == property_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Property not in watchlist")

    item.notes = body.notes
    db.commit()

    prop = db.query(Property).filter(Property.id == property_id).first()
    return _to_response(item, prop)


@router.put("/{property_id}/stage", response_model=WatchlistItemResponse)
def update_stage(
    property_id: str,
    body: WatchlistUpdateStage,
    user=Depends(get_current_user),
    db: Session = Depends(_get_db),
):
    from database.models import Property, WatchlistItem

    valid_stages = {"watching", "touring", "offer_sent", "under_contract", "closed", "passed"}
    if body.pipeline_stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {valid_stages}")

    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id, WatchlistItem.property_id == property_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Property not in watchlist")

    item.pipeline_stage = body.pipeline_stage
    db.commit()

    prop = db.query(Property).filter(Property.id == property_id).first()
    return _to_response(item, prop)
