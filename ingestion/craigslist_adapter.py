"""
Craigslist FSBO Adapter
=======================
Searches Craigslist housing-for-sale (FSBO) via HTML search pages.

WHY THIS SOURCE MATTERS:
  - Off-market FSBO deals from motivated sellers
  - Landlords testing the water before listing with an agent
  - Sellers avoiding agent commissions (= potential price advantage)
  - Estate sales and inherited properties
  - Properties not yet on MLS

COMPLIANCE NOTES:
  - Uses Craigslist's publicly available search pages
  - Parses structured JSON-LD data embedded in the page (schema.org)
  - Rate limited with generous delays (CRAIGSLIST_DELAY_SECONDS)
  - Does NOT bypass CAPTCHAs, login walls, or authentication
  - Personal use only; does not redistribute data

LIMITATIONS:
  - FSBO posts often have incomplete data (no MLS#, no sqft, etc.)
  - Addresses may be approximate or missing
  - Prices may be negotiable / aspirational
  - Listing quality varies widely — human review strongly recommended

Usage:
    adapter = CraigslistAdapter()
    listings = adapter.fetch_listings(["Richmond", "Oakland"], max_price=850000)
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any

from ingestion.base import SourceAdapter
from ingestion.normalizer import normalize

logger = logging.getLogger(__name__)

# SF Bay Area Craigslist search base
# eby = East Bay sub-area; rea = real estate for sale (by owner)
# reb = real estate by broker (also useful)
# apa = apartments / housing for rent
CL_SALE_URLS = [
    "https://sfbay.craigslist.org/search/eby/rea",  # FSBO
    "https://sfbay.craigslist.org/search/eby/reb",  # Broker listings
]

CL_RENTAL_URLS = [
    "https://sfbay.craigslist.org/search/eby/apa",  # Apartments/rentals
]

# Legacy alias
CL_SEARCH_URLS = CL_SALE_URLS

# City name to Craigslist search query
CL_CITY_QUERIES: dict[str, str] = {
    "Richmond":     "richmond",
    "San Pablo":    "san pablo",
    "El Cerrito":   "el cerrito",
    "Albany":        "albany",
    "Berkeley":     "berkeley",
    "Oakland":      "oakland",
    "Hayward":      "hayward",
    "Fremont":      "fremont",
    "San Leandro":  "san leandro",
    "Emeryville":   "emeryville",
    "Pinole":       "pinole",
    "Hercules":     "hercules",
    "Vallejo":      "vallejo",
    "Alameda":      "alameda",
}

# Regex patterns to extract data from CL post titles
_PRICE_PATTERN = re.compile(r"\$([\d,]+)")
_BEDS_PATTERN = re.compile(r"(\d+)\s*(?:br|bed|bedroom)", re.IGNORECASE)
_BATHS_PATTERN = re.compile(r"(\d+(?:\.\d)?)\s*(?:ba|bath|bathroom)", re.IGNORECASE)
_SQFT_PATTERN = re.compile(r"(\d{3,5})\s*(?:sq\s*ft|sqft|sf|ft2)", re.IGNORECASE)


class CraigslistAdapter(SourceAdapter):
    """
    Fetches FSBO and broker listings from Craigslist search pages.

    Combines data from two parsing strategies:
      1. HTML listing elements (price, title, link)
      2. JSON-LD schema.org data (beds, baths, coordinates, property type)

    Data quality is lower than MLS sources, but catches off-market deals
    that Redfin/Zillow/Realtor miss entirely.
    """

    source_name = "craigslist"

    def __init__(self, listing_type: str = "sale"):
        from config import settings
        delay = getattr(settings, "CRAIGSLIST_DELAY_SECONDS", 5.0)
        super().__init__(delay_seconds=delay)
        self._listing_type = listing_type  # "sale" or "rental"

    def fetch_listings(self, cities: list[str], max_price: float) -> list[dict[str, Any]]:
        all_listings: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for city in cities:
            query = CL_CITY_QUERIES.get(city, city.lower())
            logger.info("Fetching Craigslist FSBO for '%s' (max_price=$%s)", query, max_price)

            try:
                results = self._fetch_city(query=query, max_price=max_price, city_name=city)
                # Deduplicate within this batch
                new_results = []
                for r in results:
                    eid = r.get("external_id", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        new_results.append(r)

                logger.info("  -> %d FSBO listings from Craigslist/%s", len(new_results), city)
                all_listings.extend(new_results)
            except Exception as exc:
                logger.error("Craigslist fetch failed for %s: %s", city, exc)

            self._sleep()

        return all_listings

    def _fetch_city(self, query: str, max_price: float, city_name: str) -> list[dict[str, Any]]:
        """Fetch listings from CL search pages (sale or rental)."""
        all_results = []

        if self._listing_type == "rental":
            search_urls = CL_RENTAL_URLS
            min_price = "500"  # filter out spam/fake $1 listings
        else:
            search_urls = CL_SALE_URLS
            min_price = "100000"

        for search_url in search_urls:
            params = {
                "query": query,
                "max_price": str(int(max_price)),
                "min_price": min_price,
            }

            try:
                resp = self._get(search_url, params=params)
                text = resp.text.strip()
                if not text or len(text) < 200:
                    continue

                results = self._parse_search_page(text, city_name)
                all_results.extend(results)
            except Exception as exc:
                logger.debug("CL search failed for %s at %s: %s", query, search_url, exc)

            self._sleep()

        return all_results

    def _parse_search_page(self, html: str, fallback_city: str) -> list[dict[str, Any]]:
        """
        Parse a Craigslist search results page.

        Extracts data from two sources in the HTML:
          1. <li class="cl-static-search-result"> elements (link, title, price)
          2. <script type="application/ld+json"> (beds, baths, coords, type)
        """
        # ── Step 1: Parse HTML listing elements ──────────────────────────────
        html_listings = self._parse_html_results(html)

        # ── Step 2: Parse JSON-LD structured data ────────────────────────────
        jsonld_items = self._parse_jsonld(html)

        # ── Step 3: Merge HTML + JSON-LD by position ─────────────────────────
        # CL renders them in the same order
        results = []
        for i, html_item in enumerate(html_listings):
            jsonld = jsonld_items[i] if i < len(jsonld_items) else {}
            merged = self._merge_listing(html_item, jsonld, fallback_city)
            if merged:
                results.append(merged)

        return results

    def _parse_html_results(self, html: str) -> list[dict]:
        """Extract listing URL, title, and price from HTML result elements."""
        # Pattern: <a href="URL"><div class="title">TITLE</div><div class="details"><div class="price">PRICE</div>
        pattern = re.compile(
            r'<a\s+href="(https://sfbay\.craigslist\.org/[^"]+\.html)"[^>]*>\s*'
            r'<div\s+class="title">([^<]+)</div>\s*'
            r'<div\s+class="details">\s*'
            r'<div\s+class="price">([^<]*)</div>',
            re.DOTALL,
        )

        results = []
        for match in pattern.finditer(html):
            url = match.group(1).strip()
            title = match.group(2).strip()
            price_str = match.group(3).strip()

            # Extract CL post ID from URL
            id_match = re.search(r"/(\d{8,12})\.html", url)
            cl_id = id_match.group(1) if id_match else ""

            # Parse price
            price = None
            price_match = _PRICE_PATTERN.search(price_str)
            if price_match:
                try:
                    price = float(price_match.group(1).replace(",", ""))
                except ValueError:
                    pass

            results.append({
                "url": url,
                "title": title,
                "price": price,
                "cl_id": cl_id,
            })

        return results

    def _parse_jsonld(self, html: str) -> list[dict]:
        """Extract structured listing data from JSON-LD embedded in the page."""
        pattern = re.compile(
            r'<script\s+type="application/ld\+json">(.*?)</script>',
            re.DOTALL,
        )

        items = []
        for match in pattern.finditer(html):
            try:
                data = json.loads(match.group(1))
                # CL uses ItemList with itemListElement
                for element in data.get("itemListElement", []):
                    item = element.get("item", {})
                    items.append(item)
            except (json.JSONDecodeError, AttributeError):
                continue

        return items

    def _merge_listing(self, html_item: dict, jsonld: dict, fallback_city: str) -> dict[str, Any] | None:
        """Merge HTML-parsed and JSON-LD data into a normalized listing."""
        url = html_item.get("url", "")
        title = html_item.get("title", "")
        price = html_item.get("price")
        cl_id = html_item.get("cl_id", "")

        if not url or not price:
            return None

        # Filter obviously non-residential / spam
        if self._listing_type == "rental":
            if price < 400 or price > 10_000:
                return None
        else:
            if price < 50_000:
                return None

        # ── From JSON-LD ──
        beds = jsonld.get("numberOfBedrooms")
        baths = jsonld.get("numberOfBathroomsTotal")
        lat = jsonld.get("latitude")
        lon = jsonld.get("longitude")
        ld_name = jsonld.get("name", "")
        ld_type = jsonld.get("@type", "")

        address_data = jsonld.get("address", {})
        city = address_data.get("addressLocality", fallback_city) or fallback_city

        # Property type from JSON-LD @type
        prop_type = "SFR"
        if ld_type in ("Apartment", "ApartmentComplex"):
            prop_type = "Duplex/Multi"

        # ── Extract additional data from title ──
        if not beds:
            m = _BEDS_PATTERN.search(title)
            if m:
                beds = int(m.group(1))
        if not baths:
            m = _BATHS_PATTERN.search(title)
            if m:
                baths = float(m.group(1))

        sqft = None
        m = _SQFT_PATTERN.search(title)
        if m:
            sqft = int(m.group(1))

        # ── Address extraction ──
        address = self._extract_address(title, ld_name, city)

        # External ID
        external_id = f"CL-{cl_id}" if cl_id else f"CL-{hashlib.md5(url.encode()).hexdigest()[:12]}"

        raw = {
            "address":          address,
            "city":             city,
            "state":            "CA",
            "zip_code":         "",
            "list_price":       price,
            "beds":             beds,
            "baths":            baths,
            "sqft":             sqft,
            "lot_size_sqft":    None,
            "property_type":    prop_type,
            "year_built":       None,
            "days_on_market":   None,
            "hoa_monthly":      0,
            "status":           "active",
            "listing_remarks":  f"[CL {'Rental' if self._listing_type == 'rental' else 'FSBO'}] {title}",
            "listing_url":      url,
            "external_id":      external_id,
            "latitude":         lat,
            "longitude":        lon,
            "source":           "craigslist",
        }

        return normalize(raw, source="craigslist")

    def _extract_address(self, title: str, ld_name: str, city: str) -> str:
        """Best-effort address extraction from CL post title and JSON-LD name."""
        # Check both title and LD name for street address patterns
        for text in [title, ld_name]:
            if not text:
                continue
            # Look for "123 Main St" pattern
            addr_match = re.search(
                r"\b(\d{1,5}\s+[A-Za-z]+(?:\s+[A-Za-z]+)?\s+"
                r"(?:St|Ave|Blvd|Dr|Ln|Way|Ct|Pl|Rd|Terr?|Cir|Pkwy|Hwy|Street|Avenue|Boulevard|Drive|Lane|Court|Place|Road)"
                r"\.?)\b",
                text, re.IGNORECASE,
            )
            if addr_match:
                return addr_match.group(1).strip().rstrip(",.")

        # Try extracting from LD name which often has "737 31st St, Richmond - FOR SALE" format
        if ld_name:
            # Strip common suffixes
            cleaned = re.sub(r"\s*[-–]\s*(FOR SALE|FSBO|OPEN|NEW).*", "", ld_name, flags=re.IGNORECASE)
            cleaned = cleaned.strip().rstrip(",.")
            if cleaned and len(cleaned) > 3:
                return cleaned

        # Fallback: use title cleaned up
        cleaned = re.sub(r"\$[\d,]+", "", title)
        cleaned = re.sub(r"\d+\s*br\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\*+", "", cleaned)
        cleaned = " ".join(cleaned.split()).strip().rstrip(",.-")
        if cleaned and len(cleaned) > 5:
            return f"CL: {cleaned[:80]}"

        return f"CL FSBO in {city}"

    def close(self) -> None:
        super().close()
