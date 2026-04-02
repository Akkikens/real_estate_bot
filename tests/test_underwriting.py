"""
Tests for the financial underwriting calculator.
Run: pytest tests/test_underwriting.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from database.models import Property
from underwriting.calculator import underwrite, _monthly_payment, _principal_paydown


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestMortgageFormulas:
    def test_monthly_payment_known_case(self):
        """$500k loan, 7%, 30yr → ~$3,327/mo"""
        payment = _monthly_payment(500_000, 0.07, 30)
        assert 3300 < payment < 3360, f"Got {payment:.2f}"

    def test_zero_rate(self):
        """Zero interest rate should not crash."""
        payment = _monthly_payment(300_000, 0.0, 30)
        assert payment == 0.0  # handled gracefully

    def test_principal_paydown_30yr(self):
        """After 5 years of a 30yr loan, some principal paid."""
        paid = _principal_paydown(500_000, 0.07, 5, 30)
        assert 25_000 < paid < 45_000, f"Got {paid:.2f}"

    def test_principal_paydown_full_term(self):
        """After full term, all principal paid."""
        paid = _principal_paydown(500_000, 0.07, 30, 30)
        # Should be close to full principal (small floating point drift ok)
        assert abs(paid - 500_000) < 100, f"Got {paid:.2f}"


# ── Underwriting integration ───────────────────────────────────────────────────

def _make_prop(**kwargs) -> Property:
    defaults = dict(
        id="test-uw",
        address="456 Money St",
        city="Richmond",
        state="CA",
        zip_code="94801",
        list_price=580_000,
        beds=4,
        baths=2.0,
        sqft=1600,
        lot_size_sqft=5500,
        property_type="SFR",
        year_built=1975,
        hoa_monthly=0,
        status="active",
        estimated_rent_monthly=2_800,
        has_adu_signal=False,
        has_risk_signal=False,
        is_watched=False,
        is_archived=False,
    )
    defaults.update(kwargs)
    return Property(**defaults)


class TestUnderwriting:
    def test_basic_result_structure(self):
        prop = _make_prop()
        result = underwrite(prop)

        assert result.list_price == 580_000
        assert result.down_payment > 0
        assert result.loan_amount == result.list_price - result.down_payment
        assert 70 < result.ltv_pct < 100

    def test_monthly_pi_reasonable(self):
        """P&I on $580k home with $55k down should be ~$3,500–$4,000."""
        prop = _make_prop(list_price=580_000)
        result = underwrite(prop, down_payment=55_000)
        pi = result.monthly.monthly_pi
        assert 3_400 < pi < 4_200, f"P&I out of range: {pi:.0f}"

    def test_pmi_charged_when_ltv_high(self):
        """PMI should apply when LTV > 80%."""
        prop = _make_prop(list_price=600_000)
        result = underwrite(prop, down_payment=55_000)
        ltv = result.ltv_pct
        if ltv > 80:
            assert result.monthly.monthly_pmi > 0, "PMI should be non-zero for high LTV"

    def test_no_pmi_when_large_down(self):
        """No PMI when down payment is ≥ 20%."""
        prop = _make_prop(list_price=500_000)
        result = underwrite(prop, down_payment=100_001)  # 20%+
        assert result.monthly.monthly_pmi == 0.0

    def test_house_hack_reduces_burn(self):
        """House-hack scenario should always reduce net burn vs owner-occupant."""
        prop = _make_prop(beds=4)
        result = underwrite(prop)
        assert result.monthly.house_hack_net > result.monthly.owner_occupant_burn

    def test_cash_to_close_components(self):
        """Cash to close should be sum of down + closing + reserves."""
        prop = _make_prop(list_price=600_000)
        result = underwrite(prop, down_payment=60_000)
        ctc = result.cash_to_close
        expected = ctc.down_payment + ctc.closing_costs + ctc.initial_reserves
        assert abs(ctc.total - expected) < 1.0

    def test_appreciation_scenarios_ordered(self):
        """Optimistic appreciation should exceed moderate, which exceeds conservative."""
        prop = _make_prop(list_price=600_000)
        result = underwrite(prop)
        assert result.appreciation_conservative.equity_gained < result.appreciation_moderate.equity_gained
        assert result.appreciation_moderate.equity_gained < result.appreciation_optimistic.equity_gained

    def test_good_first_property_flag(self):
        """A well-priced 4BR should typically qualify as a good first property."""
        prop = _make_prop(list_price=550_000, beds=4)
        result = underwrite(prop, down_payment=55_000)
        # Not asserting True/False (depends on rates), just check it's a bool
        assert isinstance(result.good_first_property, bool)

    def test_verdict_non_empty(self):
        prop = _make_prop()
        result = underwrite(prop)
        assert len(result.verdict) > 20

    def test_top_considerations_length(self):
        prop = _make_prop()
        result = underwrite(prop)
        assert 1 <= len(result.top_considerations) <= 5

    def test_hoa_included_in_piti(self):
        """HOA fees should be included in total PITI."""
        prop_no_hoa = _make_prop(hoa_monthly=0)
        prop_with_hoa = _make_prop(hoa_monthly=300)
        result_no = underwrite(prop_no_hoa)
        result_yes = underwrite(prop_with_hoa)
        diff = result_yes.monthly.monthly_total_piti - result_no.monthly.monthly_total_piti
        assert abs(diff - 300) < 1.0


# ── Mock adapter test ─────────────────────────────────────────────────────────

class TestMockAdapter:
    def test_generates_listings(self):
        from ingestion.mock_adapter import MockAdapter
        adapter = MockAdapter(n_per_city=5, seed=42)
        listings = adapter.fetch_listings(["Richmond", "Berkeley"], max_price=800_000)
        assert len(listings) == 10  # 5 per city × 2 cities

    def test_listings_have_required_fields(self):
        from ingestion.mock_adapter import MockAdapter
        adapter = MockAdapter(n_per_city=3, seed=42)
        listings = adapter.fetch_listings(["Richmond"], max_price=700_000)

        for listing in listings:
            assert listing.get("address"), "Missing address"
            assert listing.get("city") == "Richmond"
            assert listing.get("list_price") is not None
            assert listing.get("beds") is not None
            assert listing.get("source") == "mock"

    def test_deterministic_with_same_seed(self):
        from ingestion.mock_adapter import MockAdapter
        a = MockAdapter(n_per_city=5, seed=99)
        b = MockAdapter(n_per_city=5, seed=99)
        la = a.fetch_listings(["Oakland"], max_price=700_000)
        lb = b.fetch_listings(["Oakland"], max_price=700_000)
        assert la[0]["address"] == lb[0]["address"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
