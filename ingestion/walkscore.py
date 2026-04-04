"""
Walk Score Enrichment
=====================
Fetches Walk Score, Transit Score, and Bike Score for properties
using the Walk Score API (https://www.walkscore.com/professional/api.php).

Requires WALKSCORE_API_KEY in .env. Free tier: 5,000 requests/day.

Updates Property.walk_score and Property.transit_score in place.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import httpx

from database.models import Property

logger = logging.getLogger(__name__)

_API_URL = "https://api.walkscore.com/score"
_API_KEY = os.getenv("WALKSCORE_API_KEY", "")


def _fetch_scores(
    lat: float, lon: float, address: str
) -> Optional[dict[str, int]]:
    """
    Call the Walk Score API and return a dict with walk_score, transit_score,
    and bike_score. Returns None on failure.
    """
    if not _API_KEY:
        return None

    params = {
        "format": "json",
        "address": address,
        "lat": str(lat),
        "lon": str(lon),
        "transit": "1",
        "bike": "1",
        "wsapikey": _API_KEY,
    }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        result: dict[str, int] = {}

        # Walk Score (always present if status == 1)
        if data.get("status") == 1:
            result["walk_score"] = int(data.get("walkscore", 0))

            # Transit Score (may not be available in all locations)
            transit = data.get("transit", {})
            if transit and "score" in transit:
                result["transit_score"] = int(transit["score"])

            # Bike Score
            bike = data.get("bike", {})
            if bike and "score" in bike:
                result["bike_score"] = int(bike["score"])

            return result
        else:
            logger.debug("Walk Score API returned status %s for %s", data.get("status"), address)
            return None

    except Exception as exc:
        logger.warning("Walk Score API failed for %s: %s", address, exc)
        return None


def enrich_walk_score(prop: Property) -> bool:
    """
    Fetch and store Walk Score + Transit Score for a single property.
    Requires lat/lon to be set on the property.

    Returns True if scores were updated, False otherwise.
    """
    if not _API_KEY:
        logger.debug("WALKSCORE_API_KEY not set — skipping Walk Score enrichment")
        return False

    if prop.walk_score is not None:
        return False  # already enriched

    lat = prop.latitude
    lon = prop.longitude
    if lat is None or lon is None:
        return False

    address = f"{prop.address}, {prop.city}, {prop.state} {prop.zip_code}"
    scores = _fetch_scores(lat, lon, address)
    if scores is None:
        return False

    prop.walk_score = scores.get("walk_score")
    prop.transit_score = scores.get("transit_score")

    logger.info(
        "Walk Score enriched: %s — Walk: %s, Transit: %s",
        prop.address,
        prop.walk_score,
        prop.transit_score,
    )
    return True


def enrich_walk_scores(db, props: list[Property], rate_limit: float = 0.5) -> int:
    """
    Batch-enrich Walk Scores for a list of properties.

    Rate-limits to stay within free tier (5k/day).
    Sleeps `rate_limit` seconds between API calls.

    Returns count of newly enriched properties.
    """
    if not _API_KEY:
        logger.info("WALKSCORE_API_KEY not set — skipping Walk Score enrichment for %d properties", len(props))
        return 0

    enriched = 0
    for prop in props:
        if prop.walk_score is not None:
            continue
        if prop.latitude is None or prop.longitude is None:
            continue

        if enriched > 0:
            time.sleep(rate_limit)

        if enrich_walk_score(prop):
            enriched += 1

    if enriched:
        db.flush()
        logger.info("Walk Score: enriched %d properties (commit deferred to caller)", enriched)

    return enriched
