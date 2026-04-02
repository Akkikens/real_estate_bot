"""
Normalizer: converts raw source dicts into a canonical schema.
Also handles deduplication against the database.

Canonical field names match the Property model.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import PriceHistory, Property

logger = logging.getLogger(__name__)

# ── Canonical schema ───────────────────────────────────────────────────────────
# All fields are optional at ingestion time; scoring will handle missing data
# gracefully by using neutral/conservative defaults.

CANONICAL_FIELDS = [
    "address", "city", "state", "zip_code",
    "latitude", "longitude",
    "list_price", "original_price",
    "beds", "baths", "sqft", "lot_size_sqft",
    "property_type", "year_built", "zoning",
    "hoa_monthly", "estimated_taxes_annual",
    "days_on_market", "status",
    "estimated_rent_monthly",
    "listing_remarks",
    "agent_name", "agent_email", "agent_phone", "brokerage",
    "source", "external_id", "listing_url",
    "walk_score", "transit_score", "bart_distance_miles",
    "school_rating", "crime_index",
]


def _clean_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _clean_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        raw = re.sub(r"[,$\s]", "", str(v))
        return float(raw) if raw else None
    except (ValueError, TypeError):
        return None


def _clean_int(v: Any) -> Optional[int]:
    f = _clean_float(v)
    return int(f) if f is not None else None


def normalize(raw: dict[str, Any], source: str) -> dict[str, Any]:
    """
    Accepts a raw dict from any adapter and returns a clean canonical dict.
    Source adapters are responsible for mapping their field names to canonical
    names before calling this, or can pass raw and rely on field aliases below.
    """
    out: dict[str, Any] = {"source": source}

    for field in CANONICAL_FIELDS:
        val = raw.get(field)
        if field in ("list_price", "original_price", "hoa_monthly",
                     "estimated_taxes_annual", "estimated_rent_monthly",
                     "latitude", "longitude", "baths",
                     "bart_distance_miles", "school_rating"):
            out[field] = _clean_float(val)
        elif field in ("beds", "sqft", "lot_size_sqft", "year_built",
                       "days_on_market", "walk_score", "transit_score", "crime_index"):
            out[field] = _clean_int(val)
        else:
            out[field] = _clean_str(val)

    # Derived: price_per_sqft
    if out.get("list_price") and out.get("sqft"):
        out["price_per_sqft"] = round(out["list_price"] / out["sqft"], 1)

    # Normalize status
    status_raw = (out.get("status") or "active").lower()
    if any(k in status_raw for k in ("pend", "under contract", "contingent")):
        out["status"] = "pending"
    elif any(k in status_raw for k in ("sold", "closed")):
        out["status"] = "sold"
    else:
        out["status"] = "active"

    # Normalize property type
    pt = (out.get("property_type") or "").upper()
    if any(k in pt for k in ("DUPLEX", "2 UNIT", "TWO-UNIT", "MULTI")):
        out["property_type"] = "Duplex/Multi"
    elif "CONDO" in pt or "TOWNHOUSE" in pt or "TOWN" in pt:
        out["property_type"] = "Condo/TH"
    else:
        out["property_type"] = "SFR"

    return out


def make_property_key(normalized: dict[str, Any]) -> str:
    """
    Create a deduplication key from address + zip.
    Used to find if we already have this property in the DB.
    """
    addr = (normalized.get("address") or "").lower().strip()
    zip_code = (normalized.get("zip_code") or "").strip()
    raw_key = f"{addr}|{zip_code}"
    return hashlib.md5(raw_key.encode()).hexdigest()


def upsert_property(db: Session, normalized: dict[str, Any]) -> tuple[Property, bool]:
    """
    Insert or update a property in the database.
    Returns (property, created_new).
    Also records price history if price changed.
    """
    # Try to find existing by external_id+source first (fastest)
    existing: Optional[Property] = None
    ext_id = normalized.get("external_id")
    source = normalized.get("source")

    if ext_id and source:
        existing = (
            db.query(Property)
            .filter(Property.external_id == ext_id, Property.source == source)
            .first()
        )

    # Fallback: match by address + zip
    if not existing:
        addr = (normalized.get("address") or "").strip()
        zip_code = (normalized.get("zip_code") or "").strip()
        if addr and zip_code:
            existing = (
                db.query(Property)
                .filter(Property.address.ilike(addr), Property.zip_code == zip_code)
                .first()
            )

    created_new = existing is None

    if existing:
        prop = existing
        old_price = prop.list_price
        new_price = normalized.get("list_price")

        # Update mutable fields
        for field in CANONICAL_FIELDS + ["price_per_sqft"]:
            val = normalized.get(field)
            if val is not None:
                setattr(prop, field, val)

        # Track price changes
        if new_price and old_price and abs(new_price - old_price) > 500:
            event = "reduced" if new_price < old_price else "increased"
            db.add(PriceHistory(property_id=prop.id, price=new_price, event=event))
            logger.info("Price %s: %s → $%s", event, prop.address, new_price)
    else:
        prop = Property(**{k: v for k, v in normalized.items() if hasattr(Property, k)})
        db.add(prop)

        # First price record
        if normalized.get("list_price"):
            db.flush()  # get prop.id
            db.add(PriceHistory(property_id=prop.id, price=normalized["list_price"], event="listed"))

    return prop, created_new
