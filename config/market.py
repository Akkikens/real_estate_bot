"""
Market Configuration
====================
Abstracts all market-specific values (state, tax rates, transit systems,
neighborhoods, price floors, etc.) so the system can expand beyond California.

Each market is a dataclass with all the per-market tunable values.
The active market is loaded from MARKET_ID in .env (default: "bay_area").

To add a new market:
  1. Create a new MarketConfig instance in MARKETS below.
  2. Set MARKET_ID=<your_market> in .env.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TransitStation:
    """A single transit station (BART, Metro, Subway, etc.)."""
    name: str
    latitude: float
    longitude: float


@dataclass
class MarketConfig:
    """All market-specific configuration in one place."""

    id: str                         # e.g. "bay_area", "los_angeles", "austin"
    display_name: str               # e.g. "SF Bay Area (East Bay)"
    state: str                      # e.g. "CA", "TX"
    timezone: str                   # e.g. "America/Los_Angeles"

    # ── Financial defaults ────────────────────────────────────────────────
    property_tax_rate: float        # e.g. 0.0125 (CA Prop 13) vs 0.025 (NJ)
    closing_cost_pct: float         # e.g. 0.025
    rent_price_ratio: float         # heuristic: monthly_rent ≈ price * this
    insurance_rate: float           # annual insurance as fraction of price

    # ── Transit system ────────────────────────────────────────────────────
    transit_system_name: str        # e.g. "BART", "Metro", "Subway"
    transit_stations: list[TransitStation] = field(default_factory=list)

    # ── City-level data ───────────────────────────────────────────────────
    # Price floors for sanity checks (city_lower -> min_price)
    city_price_floors: dict[str, float] = field(default_factory=dict)

    # City-level transit quality scores
    city_transit_scores: dict[str, float] = field(default_factory=dict)

    # City-level safety scores
    city_safety_scores: dict[str, float] = field(default_factory=dict)

    # City-level grocery walkability
    city_grocery_scores: dict[str, float] = field(default_factory=dict)

    # Average 1BR rents by city (for rental value scoring)
    city_avg_rents: dict[str, float] = field(default_factory=dict)

    # Room rental rates [low, mid, high]
    room_rental_low: float = 1_000
    room_rental_mid: float = 1_400
    room_rental_high: float = 1_800

    # ── Neighborhoods ─────────────────────────────────────────────────────
    safe_neighborhoods: dict[str, int] = field(default_factory=dict)
    unsafe_keywords: list[str] = field(default_factory=list)

    # ── Ingestion ─────────────────────────────────────────────────────────
    # Redfin region IDs for target cities
    redfin_region_ids: dict[str, int] = field(default_factory=dict)
    redfin_market_param: str = "sanfrancisco"

    # Realtor.com city slugs
    realtor_city_slugs: dict[str, str] = field(default_factory=dict)

    # Craigslist search URLs
    craigslist_sale_urls: list[str] = field(default_factory=list)
    craigslist_rental_urls: list[str] = field(default_factory=list)

    # ── Legal / disclosure ────────────────────────────────────────────────
    disclosure_forms: str = "seller disclosure statement (or equivalent state-required disclosures)"
    adu_legislation_refs: list[str] = field(default_factory=list)

    # ── Price per sqft sanity range ───────────────────────────────────────
    price_per_sqft_min: float = 100.0
    price_per_sqft_max: float = 2_500.0

    # SF proximity bonuses (only for Bay Area; empty for other markets)
    city_commute_bonuses: dict[str, tuple[float, str]] = field(default_factory=dict)


# ── Bay Area Market (default) ─────────────────────────────────────────────────

_BAY_AREA_TRANSIT = [
    TransitStation("Richmond",             37.9369, -122.3533),
    TransitStation("El Cerrito del Norte",  37.9254, -122.3172),
    TransitStation("El Cerrito Plaza",      37.9030, -122.2992),
    TransitStation("North Berkeley",        37.8740, -122.2833),
    TransitStation("Downtown Berkeley",     37.8700, -122.2681),
    TransitStation("Ashby",                 37.8529, -122.2700),
    TransitStation("MacArthur",             37.8283, -122.2671),
    TransitStation("19th St Oakland",       37.8085, -122.2690),
    TransitStation("12th St Oakland",       37.8032, -122.2717),
    TransitStation("Lake Merritt",          37.7976, -122.2653),
    TransitStation("Fruitvale",             37.7748, -122.2242),
    TransitStation("Coliseum",              37.7536, -122.1968),
    TransitStation("San Leandro",           37.7228, -122.1609),
    TransitStation("Bay Fair",              37.6970, -122.1266),
    TransitStation("Hayward",               37.6700, -122.0870),
    TransitStation("South Hayward",         37.6348, -122.0574),
    TransitStation("Union City",            37.5910, -122.0175),
    TransitStation("Fremont",               37.5574, -121.9764),
    TransitStation("Warm Springs",          37.5024, -121.9395),
    TransitStation("West Oakland",          37.8047, -122.2952),
    TransitStation("Embarcadero",           37.7929, -122.3969),
]

BAY_AREA = MarketConfig(
    id="bay_area",
    display_name="SF Bay Area (East Bay)",
    state="CA",
    timezone="America/Los_Angeles",

    property_tax_rate=0.0125,
    closing_cost_pct=0.025,
    rent_price_ratio=0.0045,
    insurance_rate=0.005,

    transit_system_name="BART",
    transit_stations=_BAY_AREA_TRANSIT,

    city_price_floors={
        "richmond": 250_000, "san pablo": 200_000, "el cerrito": 500_000,
        "pinole": 350_000, "hercules": 450_000, "martinez": 350_000,
        "concord": 350_000, "walnut creek": 600_000,
        "oakland": 300_000, "berkeley": 650_000, "albany": 750_000,
        "emeryville": 450_000, "hayward": 450_000, "san leandro": 450_000,
        "fremont": 700_000, "newark": 600_000, "union city": 550_000,
        "vallejo": 200_000, "benicia": 400_000, "fairfield": 300_000,
    },

    city_transit_scores={
        "oakland": 8, "berkeley": 8, "el cerrito": 8, "albany": 6,
        "emeryville": 6, "richmond": 7, "alameda": 5, "fremont": 7,
    },

    city_safety_scores={
        "alameda": 8.5, "albany": 8, "berkeley": 7, "el cerrito": 7.5,
        "emeryville": 6.5, "oakland": 5.5, "richmond": 5, "fremont": 7.5,
    },

    city_grocery_scores={
        "alameda": 7, "oakland": 7, "berkeley": 8, "emeryville": 8,
        "albany": 7, "el cerrito": 6, "richmond": 5,
    },

    city_avg_rents={
        "alameda": 1800, "oakland": 1700, "berkeley": 1900,
        "emeryville": 1850, "albany": 1750, "el cerrito": 1600,
        "richmond": 1400, "fremont": 1900,
    },

    room_rental_low=1_000,
    room_rental_mid=1_400,
    room_rental_high=1_800,

    safe_neighborhoods={
        "alameda": 9, "rockridge": 9, "piedmont": 9, "montclair": 9,
        "grand lake": 8, "lake merritt": 7, "temescal": 8,
        "albany": 8, "el cerrito": 8, "berkeley hills": 9,
        "north berkeley": 8, "claremont": 9, "emeryville": 7,
        "adams point": 7, "lakeshore": 8,
    },

    unsafe_keywords=[
        "east oakland", "deep east", "international blvd", "coliseum",
        "hegenberger", "elmhurst", "seminary", "brookfield",
        "98th", "105th", "ghost town",
    ],

    redfin_region_ids={
        "Richmond": 17429, "San Pablo": 17440, "El Cerrito": 17341,
        "Albany": 17278, "Berkeley": 17295, "Oakland": 17404,
        "Hayward": 17362, "Fremont": 17350, "San Leandro": 17439,
        "Emeryville": 17342, "Pinole": 17416, "Hercules": 17363,
        "Alameda": 17277,
    },
    redfin_market_param="sanfrancisco",

    realtor_city_slugs={
        "Richmond": "Richmond_CA", "San Pablo": "San-Pablo_CA",
        "El Cerrito": "El-Cerrito_CA", "Albany": "Albany_CA",
        "Berkeley": "Berkeley_CA", "Oakland": "Oakland_CA",
        "Hayward": "Hayward_CA", "Fremont": "Fremont_CA",
        "San Leandro": "San-Leandro_CA", "Emeryville": "Emeryville_CA",
        "Pinole": "Pinole_CA", "Hercules": "Hercules_CA",
        "Vallejo": "Vallejo_CA", "Concord": "Concord_CA",
        "Martinez": "Martinez_CA",
    },

    craigslist_sale_urls=[
        "https://sfbay.craigslist.org/search/eby/rea",
        "https://sfbay.craigslist.org/search/eby/reb",
    ],
    craigslist_rental_urls=[
        "https://sfbay.craigslist.org/search/eby/apa",
    ],

    disclosure_forms="Seller disclosure statement (TDS/SPQ) or equivalent CA disclosures",
    adu_legislation_refs=["SB9", "AB 68", "California ADU law"],

    price_per_sqft_min=100.0,
    price_per_sqft_max=2_500.0,

    city_commute_bonuses={
        "oakland":    (1.5, "Oakland — 12 min to SF on BART, peak rental demand."),
        "emeryville": (1.5, "Emeryville — BART + Amtrak, major employer hub, direct SF access."),
        "berkeley":   (1.2, "Berkeley — strong BART corridor, high commuter demand."),
        "albany":     (1.0, "Albany — walkable to El Cerrito/Berkeley BART, high desirability."),
        "el cerrito": (1.0, "El Cerrito — two BART stations, solid SF commute."),
        "richmond":   (0.8, "Richmond — BART + ferry terminal, undervalued SF commute access."),
        "fremont":    (0.5, "Fremont — BART terminus, 880 corridor, growing tech job base."),
    },
)


# ── Market Registry ───────────────────────────────────────────────────────────

MARKETS: dict[str, MarketConfig] = {
    "bay_area": BAY_AREA,
}


def get_market(market_id: Optional[str] = None) -> MarketConfig:
    """
    Return the MarketConfig for the given ID.
    Defaults to MARKET_ID env var, then "bay_area".
    """
    mid = market_id or os.getenv("MARKET_ID", "bay_area")
    if mid not in MARKETS:
        raise ValueError(
            f"Unknown market '{mid}'. Available: {', '.join(MARKETS.keys())}. "
            f"Set MARKET_ID in .env to one of these."
        )
    return MARKETS[mid]
