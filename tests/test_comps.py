"""
Tests for the comparable sales module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy.pool import StaticPool

from database.models import Base, Property
from scoring.comps import find_comps, comp_summary, _haversine, _similarity_score
from tests.conftest import make_prop

configure_mappers()

_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
_Session = sessionmaker(bind=_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


def _add_props(db, props):
    for p in props:
        db.add(p)
    db.flush()


class TestHaversine:
    def test_same_point(self):
        assert _haversine(37.8, -122.2, 37.8, -122.2) == 0.0

    def test_known_distance(self):
        # Oakland to Berkeley ~3-5 miles
        d = _haversine(37.8044, -122.2712, 37.8716, -122.2727)
        assert 4.0 < d < 6.0


class TestSimilarityScore:
    def test_identical_properties(self):
        p1 = make_prop(list_price=600000, beds=3, sqft=1500, year_built=1990)
        p2 = make_prop(list_price=600000, beds=3, sqft=1500, year_built=1990)
        sim, price_diff, sqft_diff, dist = _similarity_score(p1, p2)
        assert sim == 100.0
        assert price_diff == 0.0

    def test_different_price(self):
        p1 = make_prop(list_price=600000, beds=3, sqft=1500)
        p2 = make_prop(list_price=750000, beds=3, sqft=1500)
        sim, price_diff, _, _ = _similarity_score(p1, p2)
        assert sim < 100
        assert price_diff == 25.0

    def test_different_beds(self):
        p1 = make_prop(list_price=600000, beds=3)
        p2 = make_prop(list_price=600000, beds=5)
        sim, _, _, _ = _similarity_score(p1, p2)
        assert sim < 100

    def test_no_data_returns_zero(self):
        p1 = make_prop(list_price=None, beds=None, sqft=None, year_built=None)
        p2 = make_prop(list_price=None, beds=None, sqft=None, year_built=None)
        sim, _, _, _ = _similarity_score(p1, p2)
        assert sim == 0.0


class TestFindComps:
    def test_finds_similar_properties(self):
        db = _Session()
        target = make_prop(
            id="target-001", address="100 Main St", city="Oakland",
            list_price=600000, beds=3, sqft=1500, status="active",
        )
        comp1 = make_prop(
            id="comp-001", address="101 Main St", city="Oakland",
            list_price=620000, beds=3, sqft=1400, status="active",
        )
        comp2 = make_prop(
            id="comp-002", address="200 Oak Ave", city="Oakland",
            list_price=580000, beds=3, sqft=1600, status="active",
        )
        _add_props(db, [target, comp1, comp2])
        db.commit()

        comps = find_comps(db, target, limit=10)
        assert len(comps) == 2
        assert all(c.similarity > 0 for c in comps)
        db.close()

    def test_excludes_self(self):
        db = _Session()
        target = make_prop(
            id="self-001", address="100 Main St", city="Oakland",
            list_price=600000, beds=3, status="active",
        )
        _add_props(db, [target])
        db.commit()

        comps = find_comps(db, target)
        assert len(comps) == 0
        db.close()

    def test_excludes_archived(self):
        db = _Session()
        target = make_prop(
            id="t-001", address="100 Main", city="Oakland",
            list_price=600000, beds=3, status="active",
        )
        archived = make_prop(
            id="a-001", address="200 Main", city="Oakland",
            list_price=610000, beds=3, status="active", is_archived=True,
        )
        _add_props(db, [target, archived])
        db.commit()

        comps = find_comps(db, target)
        assert len(comps) == 0
        db.close()

    def test_respects_limit(self):
        db = _Session()
        target = make_prop(
            id="t-lim", address="100 Main", city="Oakland",
            list_price=600000, beds=3, status="active",
        )
        others = [
            make_prop(
                id=f"c-{i}", address=f"{i} Oak St", city="Oakland",
                list_price=600000 + i * 5000, beds=3, status="active",
            ) for i in range(20)
        ]
        _add_props(db, [target] + others)
        db.commit()

        comps = find_comps(db, target, limit=5)
        assert len(comps) <= 5
        db.close()


class TestCompSummary:
    def test_no_comps(self):
        target = make_prop(address="123 Main")
        text = comp_summary(target, [])
        assert "No comparable properties" in text

    def test_with_comps(self):
        target = make_prop(address="123 Main", city="Oakland", list_price=600000, beds=3, sqft=1500)
        db = _Session()
        Base.metadata.create_all(bind=_engine)
        comp1 = make_prop(
            id="cs-001", address="124 Main", city="Oakland",
            list_price=610000, beds=3, sqft=1500, status="active",
        )
        db.add(target)
        db.add(comp1)
        db.commit()

        comps = find_comps(db, target)
        text = comp_summary(target, comps)
        assert "Comp Analysis" in text
        assert "123 Main" in text
        db.close()
