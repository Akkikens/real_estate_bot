"""
Report Generator
================
Produces daily/weekly digest reports covering:
  1. Top 10 active opportunities (by score)
  2. Price drops in the last 7 days
  3. Best house-hack candidates
  4. Best ADU candidates
  5. Best large-lot opportunities
  6. Deals that look like traps (high risk / low score)
  7. CRM follow-up summary
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from database.models import PriceHistory, Property

logger = logging.getLogger(__name__)


def _active(db: Session):
    return db.query(Property).filter(
        Property.status == "active",
        Property.is_archived == False,
    )


def top_opportunities(db: Session, limit: int = 10) -> list[Property]:
    """Top scored active listings."""
    return (
        _active(db)
        .filter(Property.total_score.isnot(None))
        .order_by(Property.total_score.desc())
        .limit(limit)
        .all()
    )


def recent_price_drops(db: Session, days: int = 7) -> list[dict]:
    """Properties with price reductions in the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    ph_rows = (
        db.query(PriceHistory)
        .filter(PriceHistory.event == "reduced", PriceHistory.recorded_at >= cutoff)
        .all()
    )
    results = []
    for ph in ph_rows:
        prop = ph.property
        if prop and not prop.is_archived:
            results.append({"property": prop, "new_price": ph.price, "recorded_at": ph.recorded_at})
    results.sort(key=lambda x: x["property"].total_score or 0, reverse=True)
    return results


def best_house_hacks(db: Session, limit: int = 10) -> list[Property]:
    """Properties with 3+ beds, high score, and house-hack signals."""
    return (
        _active(db)
        .filter(
            Property.beds >= 3,
            Property.total_score.isnot(None),
        )
        .order_by(Property.total_score.desc())
        .limit(limit)
        .all()
    )


def best_adu_candidates(db: Session, limit: int = 10) -> list[Property]:
    """Properties with ADU signals or large lots."""
    return (
        _active(db)
        .filter(
            Property.has_adu_signal == True,
            Property.total_score.isnot(None),
        )
        .order_by(Property.total_score.desc())
        .limit(limit)
        .all()
    )


def best_large_lots(db: Session, min_sqft: int = 5500, limit: int = 10) -> list[Property]:
    """Properties with large lots sorted by score."""
    return (
        _active(db)
        .filter(
            Property.lot_size_sqft >= min_sqft,
            Property.total_score.isnot(None),
        )
        .order_by(Property.total_score.desc())
        .limit(limit)
        .all()
    )


def likely_traps(db: Session, limit: int = 5) -> list[dict]:
    """
    Properties that look risky:
      • Has risk signals in remarks
      • Low score despite potentially appealing price
      • Or extremely stale (90+ DOM) with no price drop
    """
    traps = []

    # Risk-keyword properties
    risky = (
        _active(db)
        .filter(Property.has_risk_signal == True)
        .order_by(Property.total_score.asc())
        .limit(limit)
        .all()
    )
    for prop in risky:
        traps.append({
            "property": prop,
            "reason": "Risk keywords in listing (fire damage, foundation, code violations, etc.)",
        })

    # Very stale with no notable features
    stale = (
        _active(db)
        .filter(
            Property.days_on_market >= 90,
            Property.has_adu_signal == False,
            Property.total_score < 50,
        )
        .limit(limit)
        .all()
    )
    for prop in stale:
        if prop not in [t["property"] for t in traps]:
            traps.append({
                "property": prop,
                "reason": f"Stale listing ({prop.days_on_market} DOM) with low score and no notable upside — something is likely wrong.",
            })

    return traps[:limit]


def full_report(db: Session) -> dict:
    """Compile all report sections into a single dict."""
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "top_opportunities": top_opportunities(db, 10),
        "price_drops": recent_price_drops(db, 7),
        "best_house_hacks": best_house_hacks(db, 10),
        "best_adu_candidates": best_adu_candidates(db, 10),
        "best_large_lots": best_large_lots(db, 5_500, 10),
        "likely_traps": likely_traps(db, 5),
    }
