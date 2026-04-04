"""
Tests for the scoring engine.
Run: pytest tests/test_scoring.py -v
"""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from database.models import Property
from scoring.engine import (
    score_property,
    _score_price_fit,
    _score_house_hack,
    _score_adu_upside,
    _score_deal_opportunity,
    _compute_complexity_penalty,
)


def _make_prop(**kwargs) -> Property:
    """Helper: create a minimal Property for testing."""
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


# ── Price fit tests ────────────────────────────────────────────────────────────

class TestPriceFit:
    def test_excellent_price(self):
        prop = _make_prop(list_price=450_000)  # 60% of 750k max
        score, note = _score_price_fit(prop)
        assert score == 10.0
        assert "excellent" in note.lower()

    def test_at_budget_max(self):
        prop = _make_prop(list_price=750_000)  # ~88% of 850k max
        score, note = _score_price_fit(prop)
        assert score >= 4.0  # depends on YAML price bands

    def test_over_budget(self):
        prop = _make_prop(list_price=900_000)  # ~106% of max
        score, note = _score_price_fit(prop)
        assert score <= 4.0  # penalized but may not be 0 if within stretch range

    def test_missing_price(self):
        prop = _make_prop(list_price=None)
        score, note = _score_price_fit(prop)
        assert score == 5.0  # neutral


# ── House hack tests ───────────────────────────────────────────────────────────

class TestHouseHack:
    def test_4br_high_score(self):
        prop = _make_prop(beds=4)
        score, note = _score_house_hack(prop)
        assert score >= 5.0
        assert "4BR" in note

    def test_duplex_bonus(self):
        prop = _make_prop(beds=3, property_type="Duplex/Multi")
        score, _ = _score_house_hack(prop)
        assert score >= 6.5  # 3BR + duplex bonus

    def test_separate_entrance_bonus(self):
        prop = _make_prop(
            beds=3,
            listing_remarks="3BR with separate entrance and in-law potential."
        )
        score1, _ = _score_house_hack(_make_prop(beds=3, listing_remarks="Nice 3BR."))
        score2, _ = _score_house_hack(prop)
        assert score2 > score1

    def test_1br_low_score(self):
        prop = _make_prop(beds=1)
        score, _ = _score_house_hack(prop)
        assert score < 2.0


# ── ADU tests ─────────────────────────────────────────────────────────────────

class TestAduUpside:
    def test_adu_keywords_detected(self):
        prop = _make_prop(
            listing_remarks="Huge lot! ADU potential. Junior ADU possible per SB9.",
            lot_size_sqft=7000,
        )
        score, note = _score_adu_upside(prop)
        assert score >= 7.0
        assert "ADU" in note or "adu" in note.lower()

    def test_large_lot_no_keywords(self):
        prop = _make_prop(lot_size_sqft=8000, listing_remarks="Nice home.")
        score, _ = _score_adu_upside(prop)
        assert score >= 4.0

    def test_small_lot(self):
        prop = _make_prop(lot_size_sqft=1500, listing_remarks="Cozy home.")
        score, _ = _score_adu_upside(prop)
        assert score < 4.0

    def test_sb9_mention(self):
        prop = _make_prop(
            listing_remarks="Corner lot, lot split possible under SB9.",
            lot_size_sqft=5000,
        )
        score, _ = _score_adu_upside(prop)
        assert score >= 6.0


# ── Deal opportunity tests ────────────────────────────────────────────────────

class TestDealOpportunity:
    def test_price_cut_large(self):
        prop = _make_prop(
            list_price=500_000,
            original_price=570_000,
            days_on_market=15,
        )
        score, note = _score_deal_opportunity(prop)
        assert score >= 6.0
        assert "%" in note

    def test_stale_listing(self):
        prop = _make_prop(days_on_market=75, original_price=None)
        score, _ = _score_deal_opportunity(prop)
        assert score >= 5.0

    def test_fresh_listing_lower_score(self):
        prop_fresh = _make_prop(days_on_market=3)
        prop_stale = _make_prop(days_on_market=60)
        score_fresh, _ = _score_deal_opportunity(prop_fresh)
        score_stale, _ = _score_deal_opportunity(prop_stale)
        assert score_stale > score_fresh

    def test_deal_keywords(self):
        prop = _make_prop(
            listing_remarks="Motivated seller! Priced to sell. Make offer.",
        )
        score, note = _score_deal_opportunity(prop)
        assert "motivated" in note.lower() or "priced" in note.lower() or score > 3


# ── Complexity penalty tests ───────────────────────────────────────────────────

class TestComplexityPenalty:
    def test_no_risk(self):
        prop = _make_prop(listing_remarks="Great home. Move-in ready.")
        penalty, _ = _compute_complexity_penalty(prop)
        assert penalty == 0.0

    def test_fire_damage_penalty(self):
        prop = _make_prop(listing_remarks="Fire damage throughout. Full rebuild needed.")
        penalty, note = _compute_complexity_penalty(prop)
        assert penalty >= 10.0
        assert "fire" in note.lower() or "rebuild" in note.lower()

    def test_unpermitted_penalty(self):
        prop = _make_prop(listing_remarks="Unpermitted addition in back. Sold as-is.")
        penalty, _ = _compute_complexity_penalty(prop)
        assert penalty >= 5.0

    def test_penalty_capped(self):
        prop = _make_prop(
            listing_remarks="Fire damage, foundation issues, mold, asbestos, code violation, flood zone.",
        )
        penalty, _ = _compute_complexity_penalty(prop)
        assert penalty <= 15.0  # Max cap


# ── Full score integration test ───────────────────────────────────────────────

class TestFullScore:
    def test_score_range(self):
        """Score must always be 0–100."""
        prop = _make_prop(
            list_price=500_000,
            beds=4,
            lot_size_sqft=6000,
            listing_remarks="ADU potential, separate entrance, price reduced, motivated seller.",
            days_on_market=45,
            original_price=560_000,
            bart_distance_miles=0.8,
            transit_score=70,
            school_rating=7.0,
            crime_index=30,
        )
        result = score_property(prop)
        assert 0 <= result["total_score"] <= 100

    def test_great_property_scores_high(self):
        """An ideal property for this buyer profile should score well."""
        prop = _make_prop(
            list_price=520_000,       # Under budget
            beds=4,                    # Great for house-hacking
            lot_size_sqft=7000,        # Large lot
            listing_remarks="4BR with ADU potential and separate entrance. Price reduced. Motivated seller.",
            days_on_market=40,
            original_price=580_000,
            bart_distance_miles=0.6,
            transit_score=75,
            school_rating=7.5,
            crime_index=30,
        )
        result = score_property(prop)
        assert result["total_score"] >= 70, f"Expected high score, got {result['total_score']}"
        assert result["rating"] in ("excellent", "good")

    def test_bad_property_scores_low(self):
        """A risky over-budget property should score poorly."""
        prop = _make_prop(
            list_price=900_000,       # Way over budget
            beds=1,                    # No house-hack potential
            lot_size_sqft=800,         # Tiny lot
            listing_remarks="Fire damage. Full rebuild required. Foundation issues. Code violations.",
            days_on_market=5,
            bart_distance_miles=5.0,
            school_rating=3.5,
            crime_index=80,
        )
        result = score_property(prop)
        assert result["total_score"] < 40, f"Expected low score, got {result['total_score']}"
        assert result["rating"] in ("skip", "watch")

    def test_score_updates_property_object(self):
        """score_property should update the ORM object in-place."""
        prop = _make_prop()
        assert prop.total_score is None
        score_property(prop)
        assert prop.total_score is not None
        assert prop.rating is not None
        assert prop.score_explanation is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
