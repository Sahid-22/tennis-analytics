"""Tests for configuration management."""
from __future__ import annotations
import os
import pytest
from unittest.mock import patch
from tennis_analytics.config import get_settings, Settings
from tennis_analytics.exceptions import ConfigurationError


def test_default_settings_load():
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.access_level == "trial"
    assert settings.language == "en"
    assert settings.timeout_seconds > 0
    assert settings.max_retries >= 0


def test_api_key_override():
    settings = get_settings(api_key_override="test-key-123")
    assert settings.api_key == "test-key-123"


def test_require_api_key_raises_without_key():
    with patch.dict(os.environ, {}, clear=True):
        with patch("tennis_analytics.config.load_dotenv"):
            with pytest.raises(ConfigurationError, match="SPORTRADAR_API_KEY"):
                get_settings(require_api_key=True)


def test_database_url_defaults_to_sqlite():
    settings = get_settings()
    assert "sqlite" in settings.database_url


def test_negative_timeout_raises():
    with patch.dict(os.environ, {"SPORTRADAR_TIMEOUT_SECONDS": "-1"}):
        with pytest.raises(ConfigurationError):
            get_settings()


def test_invalid_timeout_type_raises():
    with patch.dict(os.environ, {"SPORTRADAR_TIMEOUT_SECONDS": "abc"}):
        with pytest.raises(ConfigurationError):
            get_settings()
