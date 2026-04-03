"""
Tests for the enrichment module (haversine, BART distance, geocoding).
Run: pytest tests/test_enrichment.py -v
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from ingestion.enrichment import _haversine, nearest_bart_distance, BART_STATIONS


class TestHaversine:
    def test_same_point_is_zero(self):
        d = _haversine(37.87, -122.27, 37.87, -122.27)
        assert d < 0.001

    def test_known_distance(self):
        """Richmond BART to Downtown Berkeley BART is ~5 miles."""
        d = _haversine(37.9369, -122.3533, 37.8700, -122.2681)
        assert 4.0 < d < 7.0, f"Expected ~5 mi, got {d:.2f}"

    def test_symmetrical(self):
        d1 = _haversine(37.87, -122.27, 37.93, -122.35)
        d2 = _haversine(37.93, -122.35, 37.87, -122.27)
        assert abs(d1 - d2) < 0.001


class TestNearestBart:
    def test_near_richmond_station(self):
        """A point right at Richmond BART should return Richmond."""
        dist, name = nearest_bart_distance(37.9369, -122.3533)
        assert name == "Richmond"
        assert dist < 0.1

    def test_downtown_berkeley(self):
        """A point near Downtown Berkeley BART."""
        dist, name = nearest_bart_distance(37.8700, -122.2681)
        assert name == "Downtown Berkeley"
        assert dist < 0.1

    def test_all_stations_populated(self):
        """Sanity: we should have 20+ stations."""
        assert len(BART_STATIONS) >= 20

    def test_fremont_area(self):
        """A point in Fremont should find Fremont or Warm Springs."""
        dist, name = nearest_bart_distance(37.55, -121.98)
        assert name in ("Fremont", "Warm Springs")
        assert dist < 2.0


class TestBartStationCoords:
    def test_all_in_bay_area(self):
        """All station coords should be in the Bay Area lat/lon range."""
        for name, (lat, lon) in BART_STATIONS.items():
            assert 37.4 < lat < 38.0, f"{name} lat {lat} out of range"
            assert -122.5 < lon < -121.8, f"{name} lon {lon} out of range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
