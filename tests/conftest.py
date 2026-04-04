"""
Shared test fixtures and helpers for the test suite.
"""

import sys
import os

# Ensure project root is on path for all tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from database.models import Property


def make_prop(**kwargs) -> Property:
    """Create a minimal Property for testing (for-sale defaults)."""
    defaults = dict(
        id="test-id",
        address="123 Test St",
        city="Richmond",
        state="CA",
        zip_code="94801",
        list_price=550_000,
        beds=3,
        baths=2.0,
        sqft=1400,
        lot_size_sqft=5000,
        property_type="SFR",
        year_built=1970,
        days_on_market=10,
        hoa_monthly=0,
        status="active",
        listing_remarks="Nice home with ADU potential and separate entrance.",
        has_adu_signal=False,
        has_deal_signal=False,
        has_risk_signal=False,
        is_watched=False,
        is_archived=False,
    )
    defaults.update(kwargs)
    return Property(**defaults)


def make_rental(**kwargs) -> Property:
    """Create a minimal rental Property for testing."""
    defaults = dict(
        id="test-rental",
        address="123 Test Ave",
        city="Oakland",
        state="CA",
        zip_code="94609",
        list_price=1800,
        beds=1,
        baths=1.0,
        sqft=None,
        lot_size_sqft=None,
        property_type="SFR",
        listing_type="rental",
        listing_remarks="Nice 1BR apartment.",
        has_adu_signal=False,
        has_deal_signal=False,
        has_risk_signal=False,
        is_watched=False,
        is_archived=False,
    )
    defaults.update(kwargs)
    return Property(**defaults)
