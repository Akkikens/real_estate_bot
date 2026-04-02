"""
Mock Adapter
============
Generates realistic synthetic Bay Area listings for local testing.
No network calls; fully deterministic with a random seed.

Use with:  bot ingest --source mock
"""

from __future__ import annotations

import random
from typing import Any

from ingestion.base import SourceAdapter
from ingestion.normalizer import normalize

SEED = 42

# Realistic Bay Area listing templates
_STREET_TYPES = ["St", "Ave", "Blvd", "Dr", "Ln", "Way", "Ct", "Pl"]
_STREET_NAMES = [
    "Macdonald", "Barrett", "Cutting", "Giant Rd", "Ohio", "Maine", "Florida",
    "Carlson", "Potrero", "San Pablo", "Church", "Market", "Broadway", "Elm",
    "Central", "Richmond", "Hilltop", "Moeser", "San Jose", "Solano",
    "Telegraph", "Adeline", "Shattuck", "College", "Hesperian",
]

_REMARKS_TEMPLATES = [
    "Charming {beds}BR/{baths}BA {type} on a large {lot} sqft lot. Potential ADU site. Close to BART and shopping.",
    "Investor special! {beds} bed fixer with in-law unit potential. Priced to sell. Separate entrance.",
    "Well-maintained {beds}/{baths} with detached garage. Excellent rental income history. Price reduced.",
    "Two homes on one lot! Main house {beds}BR plus detached {adu}BR cottage. Duplex potential. Motivated seller.",
    "Large lot ({lot} sqft) with room to add ADU. {beds}BR SFR with updated kitchen. Near {transit}.",
    "Duplex opportunity! Both units have separate entrances. Live in one, rent the other. Strong rental demand.",
    "Fixer with great bones. {beds}BR on {lot} sqft lot. Zoned R-2 — check with city about ADU/SB9.",
    "Beautiful {beds}/{baths} fully updated. Legal in-law suite with private entrance. High rental demand area.",
    "Back on market — buyer financing fell through. Best value in {city}! Large lot, ADU possible.",
    "Price drop! Was ${orig_price:,}. Seller must move. {beds}BR/{baths}BA with 2-car garage. Excellent commute location.",
    "Solid {beds}BR investment property. All permits up to date. Current rent roll $3,200/mo. Easy to manage.",
    "SFR with detached garage (possible conversion to JADU). {lot} sqft lot. {beds} oversized bedrooms.",
    "Motivated seller priced below market. Comparable sales at ${comp:,}. Needs cosmetic work only — no major issues.",
    "Junior ADU already permitted and built! Main house {beds}BR + 1BR JADU with kitchen. Incredible value.",
]

_TRANSIT_OPTIONS = [
    "Richmond BART", "El Cerrito del Norte BART", "El Cerrito Plaza BART",
    "Ashby BART", "North Berkeley BART", "MacArthur BART", "Fruitvale BART",
    "San Leandro BART", "Bay Point BART", "I-80", "SR-4", "AC Transit hub",
]

_CITY_ZIPS = {
    "Richmond":     ["94801", "94802", "94803", "94804", "94805"],
    "San Pablo":    ["94806"],
    "El Cerrito":   ["94530"],
    "Albany":       ["94706"],
    "Berkeley":     ["94702", "94703", "94704", "94710"],
    "Oakland":      ["94601", "94603", "94606", "94608", "94609"],
    "Hayward":      ["94541", "94542", "94544", "94545"],
    "Fremont":      ["94536", "94538", "94539"],
    "San Leandro":  ["94577", "94578", "94579"],
}

_PROPERTY_TYPES = ["SFR", "SFR", "SFR", "Duplex/Multi", "Condo/TH"]  # weighted SFR


class MockAdapter(SourceAdapter):
    """Generates synthetic listings for testing and demo purposes."""

    source_name = "mock"

    def __init__(self, n_per_city: int = 8, seed: int = SEED):
        super().__init__(delay_seconds=0.0)
        self.n_per_city = n_per_city
        self._rng = random.Random(seed)

    def fetch_listings(self, cities: list[str], max_price: float) -> list[dict[str, Any]]:
        listings = []
        for city in cities:
            for i in range(self.n_per_city):
                raw = self._generate_listing(city=city, max_price=max_price, idx=i)
                listings.append(raw)
        return listings

    def _generate_listing(self, city: str, max_price: float, idx: int) -> dict[str, Any]:
        rng = self._rng
        beds = rng.choices([2, 3, 3, 4, 4, 5], weights=[5, 30, 30, 20, 10, 5])[0]
        baths = rng.choice([1.0, 1.5, 2.0, 2.0, 2.5, 3.0])
        sqft = rng.randint(beds * 250, beds * 420)
        lot_size = rng.randint(2800, 9500)
        year_built = rng.randint(1940, 2005)
        prop_type = rng.choice(_PROPERTY_TYPES)

        # Price somewhat correlated to city and size
        city_premium = {
            "Berkeley": 1.25, "Albany": 1.15, "El Cerrito": 1.10,
            "Emeryville": 1.05, "Oakland": 1.05,
            "Richmond": 0.85, "San Pablo": 0.80,
            "Hayward": 0.90, "San Leandro": 0.95, "Fremont": 1.0,
        }.get(city, 1.0)

        base_price = int(sqft * rng.uniform(300, 480) * city_premium)
        base_price = min(base_price, int(max_price * 1.05))
        # Some listings are price-dropped
        had_price_cut = rng.random() < 0.25
        orig_price = int(base_price * rng.uniform(1.03, 1.12)) if had_price_cut else base_price
        list_price = base_price

        hoa = rng.choice([0, 0, 0, 150, 250, 400]) if prop_type == "Condo/TH" else 0

        # Days on market
        dom = rng.choices(
            [rng.randint(1, 10), rng.randint(11, 30), rng.randint(31, 90), rng.randint(91, 180)],
            weights=[40, 30, 20, 10]
        )[0]

        # Remarks
        transit = rng.choice(_TRANSIT_OPTIONS)
        adu_extra = rng.randint(1, 2)
        comp = int(list_price * rng.uniform(1.02, 1.12))
        remarks_tmpl = rng.choice(_REMARKS_TEMPLATES)
        remarks = remarks_tmpl.format(
            beds=beds, baths=baths, type=prop_type, lot=lot_size,
            orig_price=orig_price, transit=transit, city=city,
            adu=adu_extra, comp=comp
        )

        street_num = rng.randint(100, 5000)
        street = f"{street_num} {rng.choice(_STREET_NAMES)} {rng.choice(_STREET_TYPES)}"
        zip_code = rng.choice(_CITY_ZIPS.get(city, ["94801"]))

        # Geo (rough Bay Area East Bay coords)
        lat = rng.uniform(37.60, 37.95)
        lon = rng.uniform(-122.45, -122.10)

        # Bart distance rough
        bart_dist = rng.uniform(0.2, 3.5)

        raw = {
            "address":          street,
            "city":             city,
            "state":            "CA",
            "zip_code":         zip_code,
            "list_price":       list_price,
            "original_price":   orig_price,
            "beds":             beds,
            "baths":            baths,
            "sqft":             sqft,
            "lot_size_sqft":    lot_size,
            "property_type":    prop_type,
            "year_built":       year_built,
            "hoa_monthly":      hoa,
            "days_on_market":   dom,
            "status":           "active",
            "listing_remarks":  remarks,
            "agent_name":       f"Agent {rng.randint(100,999)}",
            "agent_email":      f"agent{rng.randint(100,999)}@bayrealty.com",
            "agent_phone":      f"(510) 555-{rng.randint(1000,9999)}",
            "brokerage":        rng.choice(["Bay Realty", "East Bay Homes", "Compass", "Keller Williams", "RE/MAX"]),
            "source":           "mock",
            "external_id":      f"MOCK-{city[:3].upper()}-{idx:04d}",
            "listing_url":      f"https://www.redfin.com/mock/{city.lower().replace(' ','-')}/{idx}",
            "latitude":         round(lat, 6),
            "longitude":        round(lon, 6),
            "bart_distance_miles": round(bart_dist, 2),
            "walk_score":       rng.randint(40, 90),
            "transit_score":    rng.randint(35, 85),
            "school_rating":    round(rng.uniform(3.5, 8.5), 1),
            "crime_index":      rng.randint(20, 80),
        }

        return normalize(raw, source="mock")
