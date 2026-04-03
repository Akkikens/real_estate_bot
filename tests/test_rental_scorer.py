"""
Tests for the rental scorer.
Run: pytest tests/test_rental_scorer.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pytest
from database.models import Property
from scoring.rental_scorer import (
    score_rental,
    _score_amenities,
    _score_safety,
    _score_transit,
    _score_groceries,
    _score_value,
    RENTAL_WEIGHTS,
)


def _make_rental(**kwargs) -> Property:
    """Helper: create a minimal rental Property for testing."""
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


# ── Amenity tests ─────────────────────────────────────────────────────────────

class TestRentalAmenities:
    def test_in_unit_washer_dryer(self):
        prop = _make_rental(listing_remarks="1BR with in-unit washer/dryer, stainless steel appliances.")
        score, note = _score_amenities(prop)
        assert score >= 4.0
        assert "W/D" in note or "washer" in note.lower()

    def test_no_amenities_mentioned(self):
        prop = _make_rental(listing_remarks="Available now.")
        score, note = _score_amenities(prop)
        assert score < 2.0
        assert "No amenity" in note

    def test_shared_laundry(self):
        prop = _make_rental(listing_remarks="Shared laundry on site. Hardwood floors.")
        score, note = _score_amenities(prop)
        assert score > 0


# ── Safety tests ──────────────────────────────────────────────────────────────

class TestRentalSafety:
    def test_safe_neighborhood_rockridge(self):
        prop = _make_rental(listing_remarks="Beautiful unit in Rockridge, tree-lined streets.")
        score, note = _score_safety(prop)
        assert score >= 8.0

    def test_unsafe_area(self):
        prop = _make_rental(listing_remarks="Near international blvd, close to Coliseum.")
        score, note = _score_safety(prop)
        assert score <= 5.0

    def test_city_fallback_alameda(self):
        prop = _make_rental(city="Alameda", listing_remarks="Nice place.")
        score, note = _score_safety(prop)
        assert score >= 7.0  # Alameda is safe


# ── Transit tests ─────────────────────────────────────────────────────────────

class TestRentalTransit:
    def test_bart_mentioned(self):
        prop = _make_rental(listing_remarks="5 min walk to BART!")
        score, note = _score_transit(prop)
        assert score >= 9.0

    def test_bart_distance_close(self):
        prop = _make_rental(bart_distance_miles=0.3, listing_remarks="Near transit.")
        score, note = _score_transit(prop)
        assert score >= 9.0

    def test_no_transit_info(self):
        prop = _make_rental(city="Richmond", listing_remarks="Nice place.")
        score, note = _score_transit(prop)
        assert score >= 5.0  # Richmond has BART


# ── Value tests ───────────────────────────────────────────────────────────────

class TestRentalValue:
    def test_below_average_price(self):
        prop = _make_rental(city="Oakland", list_price=1000, beds=1)
        score, note = _score_value(prop)
        assert score >= 8.0

    def test_above_average_price(self):
        prop = _make_rental(city="Richmond", list_price=2500, beds=1)
        score, note = _score_value(prop)
        assert score <= 4.0

    def test_no_price(self):
        prop = _make_rental(list_price=None)
        score, note = _score_value(prop)
        assert score == 5.0


# ── Full score integration tests ─────────────────────────────────────────────

class TestRentalFullScore:
    def test_score_range(self):
        prop = _make_rental()
        result = score_rental(prop)
        assert 0 <= result["total_score"] <= 100

    def test_score_updates_property(self):
        prop = _make_rental()
        assert prop.total_score is None
        score_rental(prop)
        assert prop.total_score is not None
        assert prop.rating is not None
        assert prop.score_explanation is not None
        assert prop.score_breakdown is not None

    def test_score_breakdown_is_valid_json(self):
        prop = _make_rental()
        score_rental(prop)
        breakdown = json.loads(prop.score_breakdown)
        assert "amenities" in breakdown
        assert "safety" in breakdown
        assert "transit" in breakdown
        assert "groceries" in breakdown
        assert "value" in breakdown

    def test_great_rental_scores_well(self):
        prop = _make_rental(
            city="Berkeley",
            list_price=1200,
            beds=1,
            listing_remarks="Remodeled 1BR near BART, in-unit washer/dryer, stainless steel, dishwasher, hardwood. Quiet street near Trader Joe's.",
            bart_distance_miles=0.3,
        )
        result = score_rental(prop)
        assert result["total_score"] >= 60

    def test_bad_rental_scores_low(self):
        prop = _make_rental(
            city="Oakland",
            list_price=3000,
            beds=1,
            listing_remarks="Available now near international blvd.",
        )
        result = score_rental(prop)
        assert result["total_score"] < 50

    def test_weights_sum_to_one(self):
        total = sum(RENTAL_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
