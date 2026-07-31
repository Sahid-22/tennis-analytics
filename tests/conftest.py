"""Shared test fixtures for the tennis analytics test suite."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from tennis_analytics.database import create_database_engine, replace_all_data
from tennis_analytics.transformers import TransformedData


@pytest.fixture
def ingested_at() -> datetime:
    """Standard ingestion timestamp for tests."""
    return datetime(2026, 7, 21, tzinfo=timezone.utc)


@pytest.fixture
def sample_data(ingested_at: datetime) -> TransformedData:
    """Complete sample data for all 7 tables."""
    return TransformedData(
        categories=[
            {"category_id": "sr:category:1", "category_name": "ATP", "ingested_at": ingested_at},
            {"category_id": "sr:category:2", "category_name": "WTA", "ingested_at": ingested_at},
        ],
        competitions=[
            {
                "competition_id": "sr:competition:1",
                "competition_name": "Australian Open",
                "parent_id": None,
                "type": "doubles",
                "gender": "men",
                "level": "atp_250",
                "category_id": "sr:category:1",
                "ingested_at": ingested_at,
            },
            {
                "competition_id": "sr:competition:2",
                "competition_name": "French Open",
                "parent_id": None,
                "type": "singles",
                "gender": "women",
                "level": "grand_slam",
                "category_id": "sr:category:2",
                "ingested_at": ingested_at,
            },
        ],
        complexes=[
            {"complex_id": "sr:complex:1", "complex_name": "Melbourne Park", "ingested_at": ingested_at},
        ],
        venues=[
            {
                "venue_id": "sr:venue:1",
                "venue_name": "Rod Laver Arena",
                "city_name": "Melbourne",
                "city_id": None,
                "country_name": "Australia",
                "country_code": "AUS",
                "timezone": "Australia/Melbourne",
                "complex_id": "sr:complex:1",
                "ingested_at": ingested_at,
            },
        ],
        competitors=[
            {
                "competitor_id": "sr:competitor:1",
                "name": "Player, One",
                "country": "Croatia",
                "country_code": "HRV",
                "abbreviation": "ONE",
                "ingested_at": ingested_at,
            },
            {
                "competitor_id": "sr:competitor:2",
                "name": "Player, Two",
                "country": "Spain",
                "country_code": "ESP",
                "abbreviation": "TWO",
                "ingested_at": ingested_at,
            },
        ],
        competitor_rankings=[
            {
                "rank": 1, "movement": 2, "points": 8000,
                "competitions_played": 15, "competitor_id": "sr:competitor:1",
                "ranking_type_id": 2, "ranking_name": "ATP",
                "ranking_year": 2026, "ranking_week": 30,
                "ranking_gender": "men",
                "source_generated_at": "2026-07-21T00:00:00+00:00",
                "ingested_at": ingested_at,
            },
            {
                "rank": 2, "movement": -1, "points": 5000,
                "competitions_played": 12, "competitor_id": "sr:competitor:2",
                "ranking_type_id": 2, "ranking_name": "ATP",
                "ranking_year": 2026, "ranking_week": 30,
                "ranking_gender": "men",
                "source_generated_at": "2026-07-21T00:00:00+00:00",
                "ingested_at": ingested_at,
            },
        ],
        api_sync_log=[
            {
                "endpoint": "competitions",
                "source_generated_at": "2026-07-21T00:00:00+00:00",
                "fetched_at": ingested_at, "status_code": 200,
                "row_count": 2, "payload_sha256": "a" * 64,
            },
            {
                "endpoint": "complexes",
                "source_generated_at": "2026-07-21T00:00:00+00:00",
                "fetched_at": ingested_at, "status_code": 200,
                "row_count": 1, "payload_sha256": "b" * 64,
            },
            {
                "endpoint": "doubles_rankings",
                "source_generated_at": "2026-07-21T00:00:00+00:00",
                "fetched_at": ingested_at, "status_code": 200,
                "row_count": 2, "payload_sha256": "c" * 64,
            },
        ],
    )


@pytest.fixture
def in_memory_engine():
    """Create an in-memory SQLite engine with schema initialized."""
    engine = create_database_engine("sqlite:///:memory:")
    return engine


@pytest.fixture
def populated_engine(in_memory_engine, sample_data):
    """In-memory engine populated with sample data."""
    replace_all_data(in_memory_engine, sample_data)
    return in_memory_engine
