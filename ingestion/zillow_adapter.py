"""
Zillow Adapter (via RapidAPI)
=============================
Uses the RapidAPI Zillow endpoint for property search.

SETUP:
  1. Sign up at https://rapidapi.com/apimaker/api/zillow-com1
  2. Subscribe to the free tier (500 requests/month) or Basic ($10/mo)
  3. Copy your API key to .env:
       ZILLOW_RAPIDAPI_KEY=your_key_here

COMPLIANCE NOTES:
  - Uses a legitimate paid API, not scraping
  - Rate limited per RapidAPI plan limits
  - Configurable delay between requests (ZILLOW_DELAY_SECONDS in .env)
  - No authentication bypass or CAPTCHA circumvention

The adapter will gracefully skip if no API key is configured.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from ingestion.base import SourceAdapter
from ingestion.normalizer import normalize

logger = logging.getLogger(__name__)

# Zillow property status codes
ZILLOW_STATUS_FOR_SALE = "ForSale"

# Zillow property type mapping
ZILLOW_PROP_TYPES = {
    "SINGLE_FAMILY": "SFR",
    "MULTI_FAMILY": "Duplex/Multi",
    "CONDO": "Condo/TH",
    "TOWNHOUSE": "Condo/TH",
    "MANUFACTURED": "SFR",
    "LOT": "Land",
    "APARTMENT": "Duplex/Multi",
}

# RapidAPI Zillow endpoints
RAPIDAPI_HOST = "zillow-com1.p.rapidapi.com"
SEARCH_URL = f"https://{RAPIDAPI_HOST}/propertyExtendedSearch"
DETAIL_URL = f"https://{RAPIDAPI_HOST}/property"


class ZillowAdapter(SourceAdapter):
    """
    Fetches listings from Zillow via RapidAPI.

    Requires ZILLOW_RAPIDAPI_KEY in .env. If not set, returns empty results
    with a warning (does not crash the pipeline).

    Usage:
        adapter = ZillowAdapter()
        listings = adapter.fetch_listings(["Richmond, CA"], max_price=850000)
    """

    source_name = "zillow"

    def __init__(self):
        from config import settings
        super().__init__(delay_seconds=settings.ZILLOW_DELAY_SECONDS)
        self._api_key = os.getenv("ZILLOW_RAPIDAPI_KEY", "")

    def fetch_listings(self, cities: list[str], max_price: float) -> list[dict[str, Any]]:
        if not self._api_key:
            logger.warning(
                "ZILLOW_RAPIDAPI_KEY not set — skipping Zillow adapter. "
                "Get a free key at https://rapidapi.com/apimaker/api/zillow-com1"
            )
            return []

        all_listings: list[dict[str, Any]] = []

        for city in cities:
            logger.info("Fetching Zillow listings for %s (max_price=$%s)", city, max_price)

            try:
                results = self._search_city(city=city, max_price=max_price)
                logger.info("  -> %d listings from Zillow/%s", len(results), city)
                all_listings.extend(results)
            except Exception as exc:
                logger.error("Zillow fetch failed for %s: %s", city, exc)

            self._sleep()

        return all_listings

    def _search_city(self, city: str, max_price: float, page: int = 1) -> list[dict[str, Any]]:
        """Search Zillow for listings in a city via RapidAPI."""

        params = {
            "location": f"{city}, CA",
            "status_type": ZILLOW_STATUS_FOR_SALE,
            "home_type": "Houses,MultiFamily,Townhomes",
            "maxPrice": str(int(max_price)),
            "minBedrooms": "2",
            "sort": "Newest",
            "page": str(page),
        }

        extra_headers = {
            "x-rapidapi-key": self._api_key,
            "x-rapidapi-host": RAPIDAPI_HOST,
        }

        resp = self._get(SEARCH_URL, params=params, extra_headers=extra_headers)
        data = resp.json()

        if not data:
            logger.warning("Zillow returned empty response for %s", city)
            return []

        # Handle API error responses
        if "message" in data and "props" not in data:
            logger.warning("Zillow API error: %s", data.get("message", "unknown"))
            return []

        props = data.get("props") or []
        results = []

        for prop in props:
            try:
                normalized = self._map_property(prop)
                if normalized:
                    results.append(normalized)
            except Exception as exc:
                logger.debug("Zillow property parse error: %s | zpid=%s", exc, prop.get("zpid"))

        return results

    def _map_property(self, prop: dict) -> dict[str, Any] | None:
        """Map a Zillow API property object to canonical schema."""

        zpid = prop.get("zpid")
        if not zpid:
            return None

        price = prop.get("price")
        if not price:
            return None

        address_data = prop.get("address") or prop
        full_address = (
            prop.get("streetAddress")
            or prop.get("address", "")
        )
        if isinstance(address_data, dict):
            full_address = address_data.get("streetAddress", full_address)

        city = (
            prop.get("addressCity")
            or (address_data.get("city") if isinstance(address_data, dict) else "")
            or ""
        )
        zip_code = (
            prop.get("addressZipcode")
            or (address_data.get("zipcode") if isinstance(address_data, dict) else "")
            or ""
        )

        # Property type mapping
        ztype = prop.get("propertyType") or prop.get("homeType") or ""
        prop_type = ZILLOW_PROP_TYPES.get(ztype.upper().replace(" ", "_"), "SFR")

        # Build listing URL
        detail_url = prop.get("detailUrl") or ""
        if detail_url and not detail_url.startswith("http"):
            detail_url = f"https://www.zillow.com{detail_url}"

        # Days on Zillow
        dom = prop.get("daysOnZillow") or prop.get("timeOnZillow") or None
        if isinstance(dom, str):
            # "5 days" -> 5
            import re
            match = re.search(r"(\d+)", dom)
            dom = int(match.group(1)) if match else None

        raw = {
            "address":          full_address,
            "city":             city,
            "state":            "CA",
            "zip_code":         str(zip_code),
            "list_price":       price,
            "beds":             prop.get("bedrooms") or prop.get("beds"),
            "baths":            prop.get("bathrooms") or prop.get("baths"),
            "sqft":             prop.get("livingArea") or prop.get("area"),
            "lot_size_sqft":    prop.get("lotAreaValue") or prop.get("lotSize"),
            "property_type":    prop_type,
            "year_built":       prop.get("yearBuilt"),
            "days_on_market":   dom,
            "hoa_monthly":      prop.get("monthlyHOA") or 0,
            "status":           "active",
            "listing_remarks":  prop.get("description") or prop.get("listingSubType", {}).get("text", ""),
            "listing_url":      detail_url,
            "external_id":      str(zpid),
            "latitude":         prop.get("latitude") or prop.get("lat"),
            "longitude":        prop.get("longitude") or prop.get("long"),
            "agent_name":       prop.get("brokerName") or prop.get("listingAgent", ""),
            "source":           "zillow",
        }

        # Zillow sometimes provides rent estimate
        rent_zestimate = prop.get("rentZestimate")
        if rent_zestimate:
            raw["estimated_rent_monthly"] = rent_zestimate

        return normalize(raw, source="zillow")

    def close(self) -> None:
        super().close()
