"""
Tests for the Walk Score enrichment module.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import make_prop
from ingestion.walkscore import _fetch_scores, enrich_walk_score


class TestFetchScores:
    @patch("ingestion.walkscore._API_KEY", "")
    def test_returns_none_without_api_key(self):
        result = _fetch_scores(37.8, -122.2, "123 Main St, Oakland, CA")
        assert result is None

    @patch("ingestion.walkscore._API_KEY", "test-key")
    @patch("ingestion.walkscore.httpx.Client")
    def test_returns_scores_on_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": 1,
            "walkscore": 85,
            "transit": {"score": 72},
            "bike": {"score": 90},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = _fetch_scores(37.8, -122.2, "123 Main St")
        assert result is not None
        assert result["walk_score"] == 85
        assert result["transit_score"] == 72
        assert result["bike_score"] == 90

    @patch("ingestion.walkscore._API_KEY", "test-key")
    @patch("ingestion.walkscore.httpx.Client")
    def test_returns_none_on_bad_status(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": 2}
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.get.return_value = mock_resp
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = _fetch_scores(37.8, -122.2, "123 Main St")
        assert result is None

    @patch("ingestion.walkscore._API_KEY", "test-key")
    @patch("ingestion.walkscore.httpx.Client")
    def test_returns_none_on_exception(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("network error")
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = _fetch_scores(37.8, -122.2, "123 Main St")
        assert result is None


class TestEnrichWalkScore:
    @patch("ingestion.walkscore._API_KEY", "")
    def test_skips_without_api_key(self):
        prop = make_prop(latitude=37.8, longitude=-122.2)
        result = enrich_walk_score(prop)
        assert result is False

    @patch("ingestion.walkscore._API_KEY", "test-key")
    def test_skips_already_enriched(self):
        prop = make_prop(latitude=37.8, longitude=-122.2, walk_score=80)
        result = enrich_walk_score(prop)
        assert result is False

    @patch("ingestion.walkscore._API_KEY", "test-key")
    def test_skips_without_coords(self):
        prop = make_prop(latitude=None, longitude=None)
        result = enrich_walk_score(prop)
        assert result is False

    @patch("ingestion.walkscore._API_KEY", "test-key")
    @patch("ingestion.walkscore._fetch_scores")
    def test_enriches_property(self, mock_fetch):
        mock_fetch.return_value = {"walk_score": 75, "transit_score": 60}
        prop = make_prop(latitude=37.8, longitude=-122.2, walk_score=None)
        result = enrich_walk_score(prop)
        assert result is True
        assert prop.walk_score == 75
        assert prop.transit_score == 60

    @patch("ingestion.walkscore._API_KEY", "test-key")
    @patch("ingestion.walkscore._fetch_scores")
    def test_handles_fetch_failure(self, mock_fetch):
        mock_fetch.return_value = None
        prop = make_prop(latitude=37.8, longitude=-122.2, walk_score=None)
        result = enrich_walk_score(prop)
        assert result is False
        assert prop.walk_score is None
