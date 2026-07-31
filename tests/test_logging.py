"""Tests for logging configuration and secret redaction."""
from __future__ import annotations
from tennis_analytics.logging_config import redact_secret


def test_redact_api_key_in_url():
    text = "GET https://api.sportradar.com/?api_key=SECRETKEY123"
    result = redact_secret(text)
    assert "SECRETKEY123" not in result
    assert "***" in result


def test_redact_header_key():
    text = "x-api-key: mysecretapikey"
    result = redact_secret(text)
    assert "mysecretapikey" not in result


def test_no_redaction_needed():
    text = "Normal log message without secrets"
    result = redact_secret(text)
    assert result == text
