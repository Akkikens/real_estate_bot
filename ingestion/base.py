"""
Base adapter interface.  Every data source inherits from SourceAdapter and
implements fetch_listings().  The returned list of dicts uses the normalized
schema defined in normalizer.py.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Common headers to look like a real browser
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


class SourceAdapter(ABC):
    """Abstract base for all listing sources."""

    source_name: str = "unknown"
    delay_seconds: float = 3.0

    def __init__(self, delay_seconds: float | None = None):
        if delay_seconds is not None:
            self.delay_seconds = delay_seconds
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=20.0,
            follow_redirects=True,
        )

    @abstractmethod
    def fetch_listings(self, cities: list[str], max_price: float) -> list[dict[str, Any]]:
        """
        Fetch raw listings and return as a list of normalized dicts.
        Must respect rate limits and ToS.
        """
        ...

    def _get(self, url: str, params: dict | None = None, extra_headers: dict | None = None) -> httpx.Response:
        headers = dict(DEFAULT_HEADERS)
        if extra_headers:
            headers.update(extra_headers)
        response = self._client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response

    def _sleep(self) -> None:
        logger.debug("Rate-limit sleep: %.1fs", self.delay_seconds)
        time.sleep(self.delay_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
