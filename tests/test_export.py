"""
Tests for the export module (CSV / HTML).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from tests.conftest import make_prop
from reports.export import properties_to_csv, underwriting_to_csv, underwriting_to_html
from underwriting.calculator import underwrite


class TestPropertiesCSV:
    def test_csv_has_header_row(self):
        props = [make_prop()]
        csv = properties_to_csv(props)
        lines = csv.strip().split("\n")
        assert len(lines) == 2  # header + 1 data row
        assert "Address" in lines[0]
        assert "Price" in lines[0]

    def test_csv_contains_property_data(self):
        prop = make_prop(address="123 Oak St", city="Oakland", list_price=650000)
        csv = properties_to_csv([prop])
        assert "123 Oak St" in csv
        assert "Oakland" in csv
        assert "650000" in csv

    def test_csv_multiple_properties(self):
        props = [
            make_prop(address="111 A St"),
            make_prop(address="222 B St"),
            make_prop(address="333 C St"),
        ]
        csv = properties_to_csv(props)
        lines = csv.strip().split("\n")
        assert len(lines) == 4  # header + 3

    def test_csv_handles_missing_values(self):
        prop = make_prop(sqft=None, lot_size_sqft=None, year_built=None)
        csv = properties_to_csv([prop])
        # Should not crash
        assert "Address" in csv

    def test_csv_empty_list(self):
        csv = properties_to_csv([])
        lines = csv.strip().split("\n")
        assert len(lines) == 1  # header only


class TestUnderwritingCSV:
    def test_underwriting_csv_structure(self):
        prop = make_prop(list_price=600000, beds=3, baths=2.0, hoa_monthly=0)
        result = underwrite(prop)
        csv = underwriting_to_csv(result)
        assert "Underwriting Report" in csv
        assert "Monthly Costs" in csv
        assert "Income Scenario" in csv
        assert "Cash to Close" in csv
        assert "Verdict" in csv

    def test_underwriting_csv_contains_numbers(self):
        prop = make_prop(list_price=700000, beds=4)
        result = underwrite(prop)
        csv = underwriting_to_csv(result)
        assert "$700,000" in csv
        assert "Principal + Interest" in csv


class TestUnderwritingHTML:
    def test_html_is_valid_structure(self):
        prop = make_prop(list_price=650000, beds=4, baths=2.0, address="456 Elm St")
        result = underwrite(prop)
        html = underwriting_to_html(result, prop=prop)
        assert "<!DOCTYPE html>" in html
        assert "456 Elm St" in html
        assert "</html>" in html

    def test_html_contains_financial_data(self):
        prop = make_prop(list_price=650000, beds=3)
        result = underwrite(prop)
        html = underwriting_to_html(result, prop=prop)
        assert "Monthly Cost Breakdown" in html
        assert "Income Scenarios" in html
        assert "Cash to Close" in html
        assert "Appreciation" in html

    def test_html_verdict_section(self):
        prop = make_prop(list_price=500000, beds=4)
        result = underwrite(prop)
        html = underwriting_to_html(result, prop=prop)
        assert "verdict-badge" in html
        assert "Key Considerations" in html

    def test_html_without_prop(self):
        prop = make_prop(list_price=650000)
        result = underwrite(prop)
        html = underwriting_to_html(result, prop=None)
        assert "<!DOCTYPE html>" in html
        # Should not have property details section
        assert "Property Details" not in html

    def test_html_print_safe(self):
        """HTML should include print media query for PDF export."""
        prop = make_prop(list_price=650000)
        result = underwrite(prop)
        html = underwriting_to_html(result, prop=prop)
        assert "@media print" in html
