"""
Tests for the ingestion normalizer module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy.pool import StaticPool

from database.models import Base, Property, PriceHistory
from ingestion.normalizer import normalize, make_property_key, upsert_property

configure_mappers()

_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
_Session = sessionmaker(bind=_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


class TestNormalize:
    def test_basic_normalization(self):
        raw = {
            "address": "  123 Main St  ",
            "city": "Oakland",
            "state": "CA",
            "list_price": "$650,000",
            "beds": "3",
            "baths": "2.0",
            "sqft": "1,500",
        }
        result = normalize(raw, source="test")
        assert result["address"] == "123 Main St"
        assert result["city"] == "Oakland"
        assert result["list_price"] == 650000.0
        assert result["beds"] == 3
        assert result["baths"] == 2.0
        assert result["sqft"] == 1500
        assert result["source"] == "test"

    def test_derived_price_per_sqft(self):
        raw = {"list_price": "500000", "sqft": "1000"}
        result = normalize(raw, source="test")
        assert result["price_per_sqft"] == 500.0

    def test_status_normalization_pending(self):
        raw = {"status": "Pending Sale"}
        result = normalize(raw, source="test")
        assert result["status"] == "pending"

    def test_status_normalization_sold(self):
        raw = {"status": "Sold"}
        result = normalize(raw, source="test")
        assert result["status"] == "sold"

    def test_status_normalization_active(self):
        raw = {"status": "For Sale"}
        result = normalize(raw, source="test")
        assert result["status"] == "active"

    def test_property_type_duplex(self):
        raw = {"property_type": "Duplex"}
        result = normalize(raw, source="test")
        assert result["property_type"] == "Duplex/Multi"

    def test_property_type_condo(self):
        raw = {"property_type": "Condo"}
        result = normalize(raw, source="test")
        assert result["property_type"] == "Condo/TH"

    def test_property_type_sfr(self):
        raw = {"property_type": "Single Family"}
        result = normalize(raw, source="test")
        assert result["property_type"] == "SFR"

    def test_none_values_handled(self):
        raw = {"address": None, "list_price": None, "beds": None}
        result = normalize(raw, source="test")
        assert result["address"] is None
        assert result["list_price"] is None
        assert result["beds"] is None

    def test_empty_string_becomes_none(self):
        raw = {"address": "   ", "city": ""}
        result = normalize(raw, source="test")
        assert result["address"] is None
        assert result["city"] is None


class TestMakePropertyKey:
    def test_deterministic(self):
        n = {"address": "123 Main St", "zip_code": "94609"}
        assert make_property_key(n) == make_property_key(n)

    def test_case_insensitive(self):
        n1 = {"address": "123 MAIN ST", "zip_code": "94609"}
        n2 = {"address": "123 main st", "zip_code": "94609"}
        assert make_property_key(n1) == make_property_key(n2)

    def test_different_addresses_different_keys(self):
        n1 = {"address": "123 Main St", "zip_code": "94609"}
        n2 = {"address": "456 Oak Ave", "zip_code": "94609"}
        assert make_property_key(n1) != make_property_key(n2)


class TestUpsertProperty:
    def test_insert_new_property(self):
        db = _Session()
        normalized = {
            "address": "123 Main St",
            "city": "Oakland",
            "state": "CA",
            "zip_code": "94609",
            "list_price": 650000,
            "beds": 3,
            "baths": 2.0,
            "source": "test",
            "external_id": "TEST-001",
            "listing_url": "https://example.com/1",
            "status": "active",
        }
        prop, created = upsert_property(db, normalized)
        assert created is True
        assert prop.address == "123 Main St"
        assert prop.list_price == 650000
        db.commit()

        # Check price history was recorded
        ph = db.query(PriceHistory).filter(PriceHistory.property_id == prop.id).all()
        assert len(ph) == 1
        assert ph[0].event == "listed"
        db.close()

    def test_update_existing_property(self):
        db = _Session()
        # Insert first
        n1 = {
            "address": "123 Main St", "city": "Oakland", "state": "CA",
            "zip_code": "94609", "list_price": 650000, "source": "test",
            "external_id": "TEST-002", "status": "active",
        }
        prop1, created1 = upsert_property(db, n1)
        assert created1 is True
        db.commit()

        # Update same property (same external_id + source)
        n2 = {
            "address": "123 Main St", "city": "Oakland", "state": "CA",
            "zip_code": "94609", "list_price": 640000, "source": "test",
            "external_id": "TEST-002", "status": "active",
        }
        prop2, created2 = upsert_property(db, n2)
        assert created2 is False
        assert prop2.id == prop1.id
        assert prop2.list_price == 640000
        db.commit()
        db.close()

    def test_price_change_records_history(self):
        db = _Session()
        n1 = {
            "address": "123 Main St", "city": "Oakland", "state": "CA",
            "zip_code": "94609", "list_price": 650000, "source": "test",
            "external_id": "TEST-003", "status": "active",
        }
        prop, _ = upsert_property(db, n1)
        db.commit()

        # Price drop
        n2 = {
            "address": "123 Main St", "city": "Oakland", "state": "CA",
            "zip_code": "94609", "list_price": 620000, "source": "test",
            "external_id": "TEST-003", "status": "active",
        }
        prop, _ = upsert_property(db, n2)
        db.commit()

        ph = db.query(PriceHistory).filter(
            PriceHistory.property_id == prop.id,
            PriceHistory.event == "reduced",
        ).all()
        assert len(ph) == 1
        assert ph[0].price == 620000
        db.close()

    def test_price_increase_records_history(self):
        db = _Session()
        n1 = {
            "address": "789 Elm St", "city": "Berkeley", "state": "CA",
            "zip_code": "94702", "list_price": 600000, "source": "test",
            "external_id": "TEST-004", "status": "active",
        }
        prop, _ = upsert_property(db, n1)
        db.commit()

        n2 = {
            "address": "789 Elm St", "city": "Berkeley", "state": "CA",
            "zip_code": "94702", "list_price": 650000, "source": "test",
            "external_id": "TEST-004", "status": "active",
        }
        prop, _ = upsert_property(db, n2)
        db.commit()

        ph = db.query(PriceHistory).filter(
            PriceHistory.property_id == prop.id,
            PriceHistory.event == "increased",
        ).all()
        assert len(ph) == 1
        db.close()

    def test_dedup_by_address_zip(self):
        db = _Session()
        # Insert with external_id
        n1 = {
            "address": "100 Oak Ave", "city": "Oakland", "state": "CA",
            "zip_code": "94609", "list_price": 500000, "source": "redfin",
            "external_id": "RF-100", "status": "active",
        }
        prop1, _ = upsert_property(db, n1)
        db.commit()

        # Same address/zip but different source (no external_id match)
        n2 = {
            "address": "100 Oak Ave", "city": "Oakland", "state": "CA",
            "zip_code": "94609", "list_price": 505000, "source": "zillow",
            "external_id": "ZW-999", "status": "active",
        }
        prop2, created = upsert_property(db, n2)
        assert created is False  # dedup by address+zip
        assert prop2.id == prop1.id
        db.close()

    def test_small_price_change_no_history(self):
        """Price changes under $500 threshold should not generate history."""
        db = _Session()
        n1 = {
            "address": "200 Pine St", "city": "Oakland", "state": "CA",
            "zip_code": "94610", "list_price": 600000, "source": "test",
            "external_id": "TEST-005", "status": "active",
        }
        prop, _ = upsert_property(db, n1)
        db.commit()

        n2 = {
            "address": "200 Pine St", "city": "Oakland", "state": "CA",
            "zip_code": "94610", "list_price": 600100, "source": "test",
            "external_id": "TEST-005", "status": "active",
        }
        prop, _ = upsert_property(db, n2)
        db.commit()

        ph = db.query(PriceHistory).filter(
            PriceHistory.property_id == prop.id,
            PriceHistory.event.in_(["reduced", "increased"]),
        ).all()
        assert len(ph) == 0
        db.close()
