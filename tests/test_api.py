"""
Tests for the FastAPI backend endpoints.
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, configure_mappers

from database.models import Base, Property, PriceHistory, Underwriting, OutreachRecord, Alert, PropertyAnomaly
from api.main import app, get_db

# ── In-memory test database ──────────────────────────────────────────────────

# Force SQLAlchemy to resolve all deferred mappers (needed because
# database/models.py uses `from __future__ import annotations`).
configure_mappers()

# Use a single shared in-memory database with StaticPool to ensure
# all connections (test setup + API request threads) see the same data.
from sqlalchemy.pool import StaticPool

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_engine)


def override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables and seed a test property before each test."""
    Base.metadata.create_all(bind=_engine)
    db = _TestSession()
    # Seed a property
    prop = Property(
        id="test-001",
        address="123 Main St",
        city="Oakland",
        state="CA",
        zip_code="94609",
        list_price=650000,
        beds=4,
        baths=2.0,
        sqft=1500,
        lot_size_sqft=5000,
        property_type="SFR",
        year_built=1965,
        days_on_market=15,
        status="active",
        listing_type="sale",
        listing_remarks="Great house-hack candidate with ADU potential.",
        has_adu_signal=True,
        has_deal_signal=False,
        has_risk_signal=False,
        is_watched=False,
        is_archived=False,
        total_score=82.5,
        rating="excellent",
        bart_distance_miles=0.7,
    )
    db.add(prop)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=_engine)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestProperties:
    def test_list_properties(self):
        resp = client.get("/api/v1/properties")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["items"][0]["address"] == "123 Main St"

    def test_list_filter_city(self):
        resp = client.get("/api/v1/properties?city=Oakland")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_list_filter_city_miss(self):
        resp = client.get("/api/v1/properties?city=Nonexistent")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_filter_min_score(self):
        resp = client.get("/api/v1/properties?min_score=80")
        assert resp.json()["total"] >= 1

    def test_list_filter_min_score_high(self):
        resp = client.get("/api/v1/properties?min_score=99")
        assert resp.json()["total"] == 0

    def test_list_search_query(self):
        resp = client.get("/api/v1/properties?q=Main")
        assert resp.json()["total"] >= 1

    def test_get_property(self):
        resp = client.get("/api/v1/properties/test-001")
        assert resp.status_code == 200
        d = resp.json()
        assert d["address"] == "123 Main St"
        assert d["has_adu_signal"] is True
        assert "ADU Potential" in d["tags"]

    def test_get_property_not_found(self):
        resp = client.get("/api/v1/properties/nonexistent")
        assert resp.status_code == 404


class TestUnderwriting:
    def test_underwrite(self):
        resp = client.get("/api/v1/properties/test-001/underwrite")
        assert resp.status_code == 200
        d = resp.json()
        assert d["list_price"] == 650000
        assert d["monthly_total_piti"] > 0
        assert d["house_hack_net"] != 0
        assert isinstance(d["checks"], list)
        assert len(d["verdict"]) > 10

    def test_underwrite_custom_down(self):
        resp = client.get("/api/v1/properties/test-001/underwrite?down_payment=100000")
        assert resp.status_code == 200
        assert resp.json()["down_payment"] == 100000

    def test_underwrite_not_found(self):
        resp = client.get("/api/v1/properties/nonexistent/underwrite")
        assert resp.status_code == 404


class TestStats:
    def test_stats(self):
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200
        d = resp.json()
        assert d["total_active"] >= 1
        assert d["total_scored"] >= 1
        assert d["excellent_count"] >= 1


class TestWatchlist:
    def test_add_and_remove(self):
        # Initially not watched
        resp = client.get("/api/v1/watchlist")
        assert resp.status_code == 200
        assert len(resp.json()) == 0

        # Add to watchlist
        resp = client.post("/api/v1/watchlist/test-001")
        assert resp.status_code == 200
        assert resp.json()["status"] == "added"

        # Now it's in the watchlist
        resp = client.get("/api/v1/watchlist")
        assert len(resp.json()) == 1

        # Remove
        resp = client.delete("/api/v1/watchlist/test-001")
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"

        # Gone
        resp = client.get("/api/v1/watchlist")
        assert len(resp.json()) == 0

    def test_watchlist_not_found(self):
        resp = client.post("/api/v1/watchlist/nonexistent")
        assert resp.status_code == 404


class TestPriceDrops:
    def test_price_drops_empty(self):
        resp = client.get("/api/v1/price-drops")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
