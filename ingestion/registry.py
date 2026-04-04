"""
Adapter registry — single place to instantiate ingestion adapters by name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ingestion.base import SourceAdapter


def get_adapters(
    sources: list[str] | str,
    listing_type: str = "sale",
    *,
    allow_mock: bool = False,
) -> list["SourceAdapter"]:
    """
    Return a list of SourceAdapter instances for the requested sources.

    *sources* can be a single name (e.g. ``"redfin"``) or a list.
    The special name ``"all"`` returns every real adapter.

    Raises ValueError for unknown source names.
    """
    if isinstance(sources, str):
        sources = [sources]

    _known_sources = {"mock", "redfin", "zillow", "realtor", "craigslist", "all"}

    adapters: list["SourceAdapter"] = []

    for src in sources:
        src = src.lower().strip()

        if src not in _known_sources:
            raise ValueError(
                f"Unknown source {src!r}. "
                f"Valid sources: {', '.join(sorted(_known_sources - {'all'}))}, or 'all'."
            )

        if src == "mock" and allow_mock:
            from ingestion.mock_adapter import MockAdapter
            adapters.append(MockAdapter(n_per_city=10))

        elif src in ("redfin", "all"):
            from ingestion.redfin_adapter import RedfinAdapter
            adapters.append(RedfinAdapter(listing_type=listing_type))

        if src in ("zillow", "all") and listing_type == "sale":
            from ingestion.zillow_adapter import ZillowAdapter
            adapters.append(ZillowAdapter())

        if src in ("realtor", "all") and listing_type == "sale":
            from ingestion.realtor_adapter import RealtorAdapter
            adapters.append(RealtorAdapter())

        if src in ("craigslist", "all"):
            from ingestion.craigslist_adapter import CraigslistAdapter
            adapters.append(CraigslistAdapter(listing_type=listing_type))

    return adapters
