"""Tests for the ETL pipeline."""
from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from tennis_analytics.pipeline import RefreshResult, run_refresh
from tennis_analytics.config import get_settings


def test_refresh_result_has_required_fields():
    """Verify RefreshResult dataclass has expected structure."""
    fields = {f.name for f in RefreshResult.__dataclass_fields__.values()}
    assert "table_counts" in fields
    assert "quality_report" in fields
    assert "database_url" in fields
