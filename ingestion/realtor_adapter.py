"""
Realtor.com Adapter
===================
Uses Realtor.com's unofficial JSON API endpoints for property search.

COMPLIANCE NOTES:
  - Realtor.com serves JSON endpoints that power their own web app.
  - This adapter is for personal research use only.
  - Rate limited with configurable delays.
  - Does NOT bypass CAPTCHAs, login walls, or authentication.
  - For commercial use, use Realtor.com's official data partnerships.

The endpoints used here are the same ones the Realtor.com website calls
when you search for properties. They may change without notice.

ALTERNATIVE: RapidAPI also offers a Realtor.com API if the direct
endpoints stop working. Set REALTOR_RAPIDAPI_KEY in .env.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

from ingestion.base import SourceAdapter
from ingestion.normalizer import normalize

logger = logging.getLogger(__name__)

# Realtor.com API endpoint (same as their web app uses)
REALTOR_SEARCH_URL = "https://www.realtor.com/api/v1/hulk_main_srp"

# RapidAPI alternative
RAPIDAPI_HOST = "realtor-com4.p.rapidapi.com"
RAPIDAPI_SEARCH_URL = f"https://{RAPIDAPI_HOST}/properties/search"

# City to location slug mapping for Realtor.com
REALTOR_CITY_SLUGS: dict[str, str] = {
    "Richmond":     "Richmond_CA",
    "San Pablo":    "San-Pablo_CA",
    "El Cerrito":   "El-Cerrito_CA",
    "Albany":        "Albany_CA",
    "Berkeley":     "Berkeley_CA",
    "Oakland":      "Oakland_CA",
    "Hayward":      "Hayward_CA",
    "Fremont":      "Fremont_CA",
    "San Leandro":  "San-Leandro_CA",
    "Emeryville":   "Emeryville_CA",
    "Pinole":       "Pinole_CA",
    "Hercules":     "Hercules_CA",
    "Vallejo":      "Vallejo_CA",
    "Concord":      "Concord_CA",
    "Martinez":     "Martinez_CA",
}

# Property type mapping
REALTOR_PROP_TYPES = {
    "single_family": "SFR",
    "multi_family": "Duplex/Multi",
    "condo": "Condo/TH",
    "condos": "Condo/TH",
    "townhomes": "Condo/TH",
    "duplex_triplex": "Duplex/Multi",
    "apartment": "Duplex/Multi",
}


class RealtorAdapter(SourceAdapter):
    """
    Fetches listings from Realtor.com.

    Tries the RapidAPI endpoint first (if REALTOR_RAPIDAPI_KEY is set),
    falls back to Realtor.com's direct web API.

    Usage:
        adapter = RealtorAdapter()
        listings = adapter.fetch_listings(["Richmond", "Oakland"], max_price=850000)
    """

    source_name = "realtor"

    def __init__(self):
        from config import settings
        delay = getattr(settings, "REALTOR_DELAY_SECONDS", 4.0)
        super().__init__(delay_seconds=delay)
        self._rapidapi_key = os.getenv("REALTOR_RAPIDAPI_KEY", "")

    def fetch_listings(self, cities: list[str], max_price: float) -> list[dict[str, Any]]:
        all_listings: list[dict[str, Any]] = []

        for city in cities:
            logger.info("Fetching Realtor.com listings for %s (max_price=$%s)", city, max_price)

            try:
                if self._rapidapi_key:
                    results = self._fetch_via_rapidapi(city=city, max_price=max_price)
                else:
                    results = self._fetch_direct(city=city, max_price=max_price)
                logger.info("  -> %d listings from Realtor.com/%s", len(results), city)
                all_listings.extend(results)
            except Exception as exc:
                logger.error("Realtor.com fetch failed for %s: %s", city, exc)

            self._sleep()

        return all_listings

    # ── RapidAPI path ────────────────────────────────────────────────────────────

    def _fetch_via_rapidapi(self, city: str, max_price: float) -> list[dict[str, Any]]:
        """Fetch via RapidAPI Realtor.com endpoint."""
        slug = REALTOR_CITY_SLUGS.get(city, f"{city.replace(' ', '-')}_CA")

        params = {
            "location": slug,
            "status": "for_sale",
            "price_max": str(int(max_price)),
            "beds_min": "2",
            "sort": "newest",
            "limit": "200",
            "offset": "0",
        }

        extra_headers = {
            "x-rapidapi-key": self._rapidapi_key,
            "x-rapidapi-host": RAPIDAPI_HOST,
        }

        resp = self._get(RAPIDAPI_SEARCH_URL, params=params, extra_headers=extra_headers)
        data = resp.json()

        if not data or "data" not in data:
            logger.warning("Realtor.com RapidAPI returned no data for %s", city)
            return []

        properties = []
        results = data.get("data", {}).get("results", [])
        if isinstance(results, list):
            for prop in results:
                try:
                    normalized = self._map_rapidapi_property(prop, city)
                    if normalized:
                        properties.append(normalized)
                except Exception as exc:
                    logger.debug("Realtor.com parse error: %s", exc)

        return properties

    def _map_rapidapi_property(self, prop: dict, fallback_city: str) -> dict[str, Any] | None:
        """Map a RapidAPI Realtor.com result to canonical schema."""
        location = prop.get("location", {})
        address_data = location.get("address", {})

        address = address_data.get("line", "")
        city = address_data.get("city", fallback_city)
        state = address_data.get("state_code", "CA")
        zip_code = address_data.get("postal_code", "")

        description = prop.get("description", {})
        price = prop.get("list_price") or description.get("list_price")
        if not price or not address:
            return None

        beds = description.get("beds") or prop.get("beds")
        baths = description.get("baths") or prop.get("baths")
        sqft = description.get("sqft") or prop.get("sqft")
        lot_sqft = description.get("lot_sqft") or prop.get("lot_sqft")
        year_built = description.get("year_built")
        prop_type_raw = description.get("type", "single_family")
        prop_type = REALTOR_PROP_TYPES.get(prop_type_raw.lower(), "SFR")

        # Listing ID
        property_id = prop.get("property_id", "")
        listing_id = prop.get("listing_id", "") or property_id

        # URL
        permalink = prop.get("permalink", "")
        listing_url = f"https://www.realtor.com/realestateandhomes-detail/{permalink}" if permalink else ""

        # Agent info
        advertisers = prop.get("advertisers", [])
        agent_name = ""
        agent_email = ""
        agent_phone = ""
        brokerage = ""
        if advertisers:
            agent = advertisers[0]
            agent_name = agent.get("name", "")
            phones = agent.get("phones", [])
            if phones:
                agent_phone = phones[0].get("number", "")
            agent_email = agent.get("email", "")
            brokerage = agent.get("broker", {}).get("name", "")

        # Days on market
        dom = prop.get("list_date")
        days_on_market = None
        if dom:
            from datetime import datetime, timezone
            try:
                list_date = datetime.fromisoformat(dom.replace("Z", "+00:00"))
                days_on_market = (datetime.now(timezone.utc) - list_date).days
            except (ValueError, TypeError):
                pass

        # Coordinates
        coord = location.get("coordinate", {}) or {}
        lat = coord.get("lat")
        lon = coord.get("lon")

        raw = {
            "address":          address,
            "city":             city,
            "state":            state,
            "zip_code":         str(zip_code),
            "list_price":       price,
            "beds":             beds,
            "baths":            baths,
            "sqft":             sqft,
            "lot_size_sqft":    lot_sqft,
            "property_type":    prop_type,
            "year_built":       year_built,
            "days_on_market":   days_on_market,
            "hoa_monthly":      prop.get("hoa", {}).get("value") if isinstance(prop.get("hoa"), dict) else 0,
            "status":           "active",
            "listing_remarks":  description.get("text", ""),
            "listing_url":      listing_url,
            "external_id":      str(listing_id),
            "latitude":         lat,
            "longitude":        lon,
            "agent_name":       agent_name,
            "agent_email":      agent_email,
            "agent_phone":      agent_phone,
            "brokerage":        brokerage,
            "source":           "realtor",
        }

        # Rent estimate if available
        rental = prop.get("rental_estimate")
        if rental and isinstance(rental, dict):
            raw["estimated_rent_monthly"] = rental.get("estimate")

        return normalize(raw, source="realtor")

    # ── Direct web API path ──────────────────────────────────────────────────────

    def _fetch_direct(self, city: str, max_price: float) -> list[dict[str, Any]]:
        """
        Fetch from Realtor.com's direct web API.
        This is the same endpoint their React frontend calls.
        """
        slug = REALTOR_CITY_SLUGS.get(city, f"{city.replace(' ', '-')}_CA")

        # Realtor.com uses a GraphQL-like query via their hulk endpoint
        # Fallback: use their search page JSON
        search_url = f"https://www.realtor.com/api/v1/rdc_search_srp"

        params = {
            "client_id": "rdc-search-for-sale-search",
            "schema": "vesta",
        }

        # The request body follows Realtor.com's internal search schema
        payload = {
            "query": {
                "status": ["for_sale"],
                "primary": True,
            },
            "limit": 200,
            "offset": 0,
            "sort": {"field": "list_date", "direction": "desc"},
        }

        # Direct API is fragile — try the simpler listing page approach
        try:
            listing_url = f"https://www.realtor.com/realestateandhomes-search/{slug}/beds-2/price-na-{int(max_price)}/type-single-family-home,multi-family-home,townhomes/pnd-hide"

            resp = self._get(listing_url, extra_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            })

            # Try to extract JSON data from the page's __NEXT_DATA__ script
            text = resp.text
            properties = self._extract_next_data(text, city)
            return properties

        except Exception as exc:
            logger.warning(
                "Realtor.com direct fetch failed for %s: %s. "
                "Consider setting REALTOR_RAPIDAPI_KEY for more reliable access.",
                city, exc
            )
            return []

    def _extract_next_data(self, html: str, fallback_city: str) -> list[dict[str, Any]]:
        """Extract listing data from Realtor.com's __NEXT_DATA__ JSON blob."""
        import json

        # Find the __NEXT_DATA__ script tag
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            logger.debug("No __NEXT_DATA__ found in Realtor.com response")
            return []

        try:
            next_data = json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.debug("Failed to parse __NEXT_DATA__ JSON")
            return []

        # Navigate to property results
        # Structure: props.pageProps.properties or similar
        page_props = next_data.get("props", {}).get("pageProps", {})

        # Try different paths where listings might be
        properties_raw = (
            page_props.get("properties", [])
            or page_props.get("searchResults", {}).get("home_search", {}).get("results", [])
            or page_props.get("listings", [])
        )

        results = []
        for prop in properties_raw:
            try:
                normalized = self._map_web_property(prop, fallback_city)
                if normalized:
                    results.append(normalized)
            except Exception as exc:
                logger.debug("Realtor.com web parse error: %s", exc)

        return results

    def _map_web_property(self, prop: dict, fallback_city: str) -> dict[str, Any] | None:
        """Map Realtor.com web page property data to canonical schema."""
        # Web data format is similar to RapidAPI but with some differences
        location = prop.get("location", {})
        address_data = location.get("address", {})

        address = address_data.get("line", prop.get("address", ""))
        if not address:
            return None

        city = address_data.get("city", fallback_city)
        zip_code = address_data.get("postal_code", "")

        description = prop.get("description", {})
        if isinstance(description, str):
            # Sometimes description is just the text
            listing_text = description
            description = {}
        else:
            listing_text = description.get("text", "")

        price = prop.get("list_price") or description.get("list_price")
        if not price:
            return None

        beds = description.get("beds") or prop.get("beds")
        baths = description.get("baths") or prop.get("baths")
        sqft = description.get("sqft") or prop.get("sqft")
        lot_sqft = description.get("lot_sqft") or prop.get("lot_sqft")

        prop_type_raw = description.get("type", "single_family")
        prop_type = REALTOR_PROP_TYPES.get(str(prop_type_raw).lower(), "SFR")

        property_id = prop.get("property_id", "")
        permalink = prop.get("permalink", "")
        listing_url = f"https://www.realtor.com/realestateandhomes-detail/{permalink}" if permalink else ""

        coord = location.get("coordinate", {}) or {}

        raw = {
            "address":          address,
            "city":             city,
            "state":            "CA",
            "zip_code":         str(zip_code),
            "list_price":       price,
            "beds":             beds,
            "baths":            baths,
            "sqft":             sqft,
            "lot_size_sqft":    lot_sqft,
            "property_type":    prop_type,
            "year_built":       description.get("year_built"),
            "days_on_market":   None,
            "hoa_monthly":      0,
            "status":           "active",
            "listing_remarks":  listing_text,
            "listing_url":      listing_url,
            "external_id":      str(property_id),
            "latitude":         coord.get("lat"),
            "longitude":        coord.get("lon"),
            "source":           "realtor",
        }

        return normalize(raw, source="realtor")

    def close(self) -> None:
        super().close()
