"""
Property enrichment — backfill missing data on listings that lack structured fields.

The first (and highest-value) enrichment is BART station distance.
Craigslist listings rarely carry structured transit data, so we geocode the
address and compute haversine distance to every relevant BART station.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Optional

import httpx

from database.models import Property

log = logging.getLogger(__name__)

# ── BART station coordinates (East Bay + key SF stations) ────────────────────
# Source: BART system map / Google Maps, rounded to 4 decimal places.

BART_STATIONS: dict[str, tuple[float, float]] = {
    "Richmond":             (37.9369, -122.3533),
    "El Cerrito del Norte": (37.9254, -122.3172),
    "El Cerrito Plaza":     (37.9030, -122.2992),
    "North Berkeley":       (37.8740, -122.2833),
    "Downtown Berkeley":    (37.8700, -122.2681),
    "Ashby":                (37.8529, -122.2700),
    "MacArthur":            (37.8283, -122.2671),
    "19th St Oakland":      (37.8085, -122.2690),
    "12th St Oakland":      (37.8032, -122.2717),
    "Lake Merritt":         (37.7976, -122.2653),
    "Fruitvale":            (37.7748, -122.2242),
    "Coliseum":             (37.7536, -122.1968),
    "San Leandro":          (37.7228, -122.1609),
    "Bay Fair":             (37.6970, -122.1266),
    "Hayward":              (37.6700, -122.0870),
    "South Hayward":        (37.6348, -122.0574),
    "Union City":           (37.5910, -122.0175),
    "Fremont":              (37.5574, -121.9764),
    "Warm Springs":         (37.5024, -121.9395),
    "West Oakland":         (37.8047, -122.2952),
    "Embarcadero":          (37.7929, -122.3969),
}

# ── Haversine helper ─────────────────────────────────────────────────────────

_EARTH_RADIUS_MI = 3958.8  # mean radius in miles


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in miles between two (lat, lon) points."""
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_MI * math.asin(math.sqrt(a))


def nearest_bart_distance(lat: float, lon: float) -> tuple[float, str]:
    """Return (distance_miles, station_name) to the closest BART station."""
    best_dist = float("inf")
    best_name = ""
    for name, (slat, slon) in BART_STATIONS.items():
        d = _haversine(lat, lon, slat, slon)
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_dist, best_name


# ── Geocoding via OpenStreetMap Nominatim ────────────────────────────────────

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "RealEstateBot/1.0 (personal project; akshay)"


def _geocode(address: str, city: str) -> Optional[tuple[float, float]]:
    """
    Geocode an address using the free Nominatim API.
    Returns (lat, lon) or None on failure.
    """
    query = f"{address}, {city}, CA"
    params = {"q": query, "format": "jsonv2", "limit": 1}
    headers = {"User-Agent": _USER_AGENT}

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(_NOMINATIM_URL, params=params, headers=headers)
            resp.raise_for_status()
            results = resp.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as exc:
        log.warning("Geocoding failed for %r: %s", query, exc)

    return None


# ── Public API ───────────────────────────────────────────────────────────────


def enrich_bart_distance(prop: Property) -> Optional[float]:
    """
    Compute and store the distance (in miles) from *prop* to the nearest
    BART station.  Geocodes if lat/lon are missing.

    Updates ``prop.bart_distance_miles`` (and ``prop.latitude`` /
    ``prop.longitude`` if they were filled by geocoding).

    Returns the distance in miles, or None if the location could not be
    determined.
    """
    lat = prop.latitude
    lon = prop.longitude

    # Geocode if coordinates are missing
    needs_geocode = lat is None or lon is None
    if needs_geocode:
        result = _geocode(prop.address, prop.city)
        if result is None:
            log.info("Could not geocode %s, %s — skipping BART enrichment", prop.address, prop.city)
            return None
        lat, lon = result
        prop.latitude = lat
        prop.longitude = lon

    distance, station = nearest_bart_distance(lat, lon)
    prop.bart_distance_miles = round(distance, 2)
    log.info(
        "Enriched %s — %.2f mi to %s%s",
        prop.address,
        distance,
        station,
        " (geocoded)" if needs_geocode else "",
    )
    return distance


def enrich_properties(db, props: list[Property]) -> int:
    """
    Enrich a batch of Property objects that are missing ``bart_distance_miles``.

    * Skips properties that already have a value.
    * Sleeps 1 s between geocoding requests to respect Nominatim rate limits.
    * Commits the session once at the end.

    Returns the count of newly enriched properties.
    """
    enriched = 0
    needed_geocode_last = False

    for prop in props:
        if prop.bart_distance_miles is not None:
            continue

        # Rate-limit only when the previous call required a geocode request,
        # since haversine-only calls are instant and don't hit any API.
        needs_geocode = prop.latitude is None or prop.longitude is None
        if needs_geocode and needed_geocode_last:
            time.sleep(1)

        result = enrich_bart_distance(prop)
        needed_geocode_last = needs_geocode

        if result is not None:
            enriched += 1

    if enriched:
        log.info("Enriched %d properties (commit deferred to caller)", enriched)

    return enriched
