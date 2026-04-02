"""
Redfin Adapter
==============
Uses Redfin's unofficial-but-widely-used GIS search API.

COMPLIANCE NOTES:
  • Redfin's ToS prohibits automated scraping for commercial use.
  • This adapter is for personal research use only.
  • It respects rate limits (configurable delay between requests).
  • It does NOT bypass CAPTCHAs or authentication.
  • If Redfin adds rate-limit headers (Retry-After), they are respected.
  • For production / commercial use, obtain a Redfin data partnership or
    use their official Data Center (https://www.redfin.com/news/data-center/).

The search URL and response format were observed from Redfin's own web app
and are used here solely to power a personal property search tool.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from config import settings
from ingestion.base import SourceAdapter
from ingestion.normalizer import normalize

logger = logging.getLogger(__name__)

# Redfin region IDs for target Bay Area cities (region_type=6 = city)
# Run `_lookup_region(city)` to find the correct ID for other cities.
REDFIN_CITY_REGION_IDS: dict[str, int] = {
    "Richmond":     17429,
    "San Pablo":    17440,
    "El Cerrito":   17341,
    "Albany":       17278,
    "Berkeley":     17295,
    "Oakland":      17404,
    "Hayward":      17362,
    "Fremont":      17350,
    "San Leandro":  17439,
    "Emeryville":   17342,
    "Pinole":       17416,
    "Hercules":     17363,
}

SEARCH_URL = "https://www.redfin.com/stingray/api/gis-csv"
REGION_LOOKUP_URL = "https://www.redfin.com/stingray/do/location-autocomplete"

# ── Recommended first-run cities (lower prices, more realistic for budget) ────
# Start here before expanding to Albany/Berkeley/Fremont where prices are 2×+
RECOMMENDED_START_CITIES = [
    "Richmond", "San Pablo", "Hayward", "Pinole", "Hercules", "San Leandro",
]


class RedfinAdapter(SourceAdapter):
    """
    Fetches active residential listings from Redfin for target cities.

    IMPORTANT — Getting real data:
    Redfin may return empty results or redirect to a CAPTCHA if requests look
    automated. If you get 0 listings, try one of these:

    Option A (easiest): Export directly from Redfin.com
      1. Go to https://www.redfin.com/city/17429/CA/Richmond
      2. Set filters: 2+ beds, max price $750k, for sale
      3. Click "Download All" (bottom of results) → saves a CSV
      4. Run: python3 main.py import-csv path/to/redfin_download.csv

    Option B: Add your browser cookies to .env
      1. Open redfin.com in Chrome, open DevTools → Application → Cookies
      2. Copy the value of the "RF_BROWSER_ID" and "RF_AUTH_TOKEN" cookies
      3. Add to .env:
           REDFIN_COOKIE=RF_BROWSER_ID=xxx; RF_AUTH_TOKEN=yyy
      The adapter will pass these with every request.

    Usage:
        adapter = RedfinAdapter()
        listings = adapter.fetch_listings(["Richmond", "El Cerrito"], max_price=700000)
    """

    source_name = "redfin"

    def __init__(self):
        super().__init__(delay_seconds=settings.REDFIN_DELAY_SECONDS)
        # Optional: pass browser cookies from .env to avoid bot detection
        self._cookie = os.getenv("REDFIN_COOKIE", "")

    def fetch_listings(self, cities: list[str], max_price: float) -> list[dict[str, Any]]:
        all_listings: list[dict[str, Any]] = []

        for city in cities:
            region_id = REDFIN_CITY_REGION_IDS.get(city)
            if not region_id:
                logger.warning("No Redfin region ID for city: %s — skipping", city)
                continue

            logger.info("Fetching Redfin listings for %s (region=%s, max_price=$%s)", city, region_id, max_price)

            try:
                rows = self._fetch_city(region_id=region_id, max_price=max_price)
                logger.info("  → %d listings from Redfin/%s", len(rows), city)
                all_listings.extend(rows)
            except Exception as exc:
                logger.error("Redfin fetch failed for %s: %s", city, exc)

            self._sleep()

        return all_listings

    def _fetch_city(self, region_id: int, max_price: float) -> list[dict[str, Any]]:
        """Fetch CSV data from Redfin's GIS endpoint and parse into dicts."""

        params = {
            "al": 1,                    # active listings
            "market": "sanfrancisco",
            "max_price": int(max_price),
            "min_beds": 2,
            "num_homes": 350,
            "ord": "redfin-recommended-asc",
            "page_number": 1,
            "region_id": region_id,
            "region_type": 6,           # 6 = city
            "sf": "1,2,3,5,6,7",       # status flags: active + coming soon
            "start": 0,
            "status": 9,
            "uipt": "1,2,3",            # 1=SFR, 2=Condo, 3=Townhouse; add 4,5,6 for multi-family
            "v": 8,
        }

        extra_headers = {}
        if self._cookie:
            extra_headers["Cookie"] = self._cookie

        resp = self._get(SEARCH_URL, params=params, extra_headers=extra_headers)

        # Detect empty/blocked response
        text = resp.text.strip()
        if not text or len(text) < 50:
            logger.warning(
                "Redfin returned empty response for region %s. "
                "This usually means bot detection triggered. "
                "See the IMPORTANT note in RedfinAdapter docstring for solutions.",
                region_id,
            )
            return []

        return self._parse_csv(text)

    def _parse_csv(self, csv_text: str) -> list[dict[str, Any]]:
        """Parse Redfin CSV export into normalized property dicts."""
        import csv
        import io

        # Redfin prepends a disclaimer line; skip it
        lines = csv_text.strip().splitlines()
        if lines and lines[0].startswith("SOLD"):
            lines = lines[1:]

        if not lines:
            return []

        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        results = []

        for row in reader:
            try:
                normalized = self._map_row(row)
                results.append(normalized)
            except Exception as exc:
                logger.debug("Row parse error: %s | %s", exc, row)

        return results

    def _map_row(self, row: dict[str, str]) -> dict[str, Any]:
        """Map Redfin CSV columns to canonical schema and normalize."""
        # Redfin CSV column names (as of 2024–2025)
        raw = {
            "address":          row.get("ADDRESS") or row.get("Address"),
            "city":             row.get("CITY") or row.get("City"),
            "state":            row.get("STATE OR PROVINCE") or "CA",
            "zip_code":         row.get("ZIP OR POSTAL CODE") or row.get("Zip"),
            "list_price":       row.get("PRICE") or row.get("Price"),
            "beds":             row.get("BEDS") or row.get("Beds"),
            "baths":            row.get("BATHS") or row.get("Baths"),
            "sqft":             row.get("SQUARE FEET") or row.get("Sqft"),
            "lot_size_sqft":    row.get("LOT SIZE") or row.get("Lot Size"),
            "property_type":    row.get("PROPERTY TYPE") or row.get("Property Type"),
            "year_built":       row.get("YEAR BUILT") or row.get("Year Built"),
            "days_on_market":   row.get("DAYS ON MARKET") or row.get("Days on Market"),
            "hoa_monthly":      row.get("HOA/MONTH") or row.get("HOA"),
            "status":           row.get("STATUS") or "active",
            "listing_remarks":  row.get("REMARKS") or row.get("Description"),
            "listing_url":      row.get("URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis for info on how Redfin values properties)")
                                or row.get("URL"),
            "external_id":      row.get("MLS#") or row.get("MLS Number"),
            "latitude":         row.get("LATITUDE") or row.get("Latitude"),
            "longitude":        row.get("LONGITUDE") or row.get("Longitude"),
            "source":           "redfin",
        }

        return normalize(raw, source="redfin")

    def lookup_region_id(self, city: str, state: str = "CA") -> int | None:
        """Helper to find region_id for a city not in our static dict."""
        try:
            params = {
                "location": f"{city}, {state}",
                "v": 2,
                "al": 1,
                "mrs": 1,
            }
            resp = self._get(REGION_LOOKUP_URL, params=params)
            # Response starts with "{}&&" (JSONP prefix)
            text = resp.text
            if text.startswith("{}&&"):
                text = text[4:]
            data = json.loads(text)
            for item in data.get("payload", {}).get("sections", []):
                for r in item.get("rows", []):
                    if r.get("type") == "6":  # city type
                        return int(r["id"]["tableId"])
        except Exception as exc:
            logger.error("Region lookup failed: %s", exc)
        return None
