"""Tests for the Sportradar API client."""
from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from tennis_analytics.api_client import SportradarTennisClient, SportradarAPIError, ENDPOINTS
from tennis_analytics.config import get_settings


@pytest.fixture
def mock_settings():
    settings = get_settings(api_key_override="test-key")
    return settings


def test_client_requires_api_key():
    settings = get_settings()
    if not settings.api_key:
        with pytest.raises(ValueError, match="API key"):
            SportradarTennisClient(settings)


def test_client_rejects_unknown_endpoint(mock_settings):
    client = SportradarTennisClient(mock_settings)
    with pytest.raises(ValueError, match="Unknown endpoint"):
        client.fetch("nonexistent")


def test_client_sets_correct_headers(mock_settings):
    client = SportradarTennisClient(mock_settings)
    assert client.session.headers["x-api-key"] == "test-key"
    assert client.session.headers["accept"] == "application/json"


def test_client_base_url_format(mock_settings):
    client = SportradarTennisClient(mock_settings)
    assert "trial" in client.base_url
    assert "v3" in client.base_url
    assert "en" in client.base_url


def test_endpoints_contains_expected_keys():
    assert "competitions" in ENDPOINTS
    assert "complexes" in ENDPOINTS
    assert "doubles_rankings" in ENDPOINTS


@patch("tennis_analytics.api_client.requests.Session")
def test_fetch_retries_on_429(mock_session_cls, mock_settings):
    mock_session = MagicMock()
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"retry-after": "0"}
    mock_response_ok = MagicMock()
    mock_response_ok.status_code = 200
    mock_response_ok.json.return_value = {"competitions": []}
    mock_response_ok.raise_for_status = MagicMock()
    mock_session.get.side_effect = [mock_response_429, mock_response_ok]
    mock_session.headers = {}
    mock_session_cls.return_value = mock_session
    # Test with manual settings to have 0-second retry
    client = SportradarTennisClient(mock_settings)
    client.session = mock_session
    result = client.fetch("competitions")
    assert result.status_code == 200


def test_client_context_manager(mock_settings):
    with SportradarTennisClient(mock_settings) as client:
        assert client is not None
        assert hasattr(client, 'session')
