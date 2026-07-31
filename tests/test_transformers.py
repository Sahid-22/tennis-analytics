"""Tests for data transformers."""
from __future__ import annotations
import pytest
from datetime import datetime, timezone
from tennis_analytics.transformers import (
    transform_payloads,
    transform_competitions,
    transform_complexes,
    transform_doubles_rankings,
    TransformedData,
)


def test_transform_payloads_complete(ingested_at):
    payloads = {
        "competitions": {
            "competitions": [
                {
                    "id": "sr:competition:1",
                    "name": "Example Open",
                    "type": "doubles",
                    "gender": "men",
                    "category": {"id": "sr:category:1", "name": "ATP"},
                }
            ],
        },
        "complexes": {
            "complexes": [
                {
                    "id": "sr:complex:1",
                    "name": "Nacional",
                    "venues": [
                        {
                            "id": "sr:venue:1",
                            "name": "Centre Court",
                            "city_name": "Santiago",
                            "country_name": "Chile",
                            "country_code": "CHL",
                            "timezone": "America/Santiago",
                        }
                    ],
                }
            ],
        },
        "doubles_rankings": {
            "rankings": [
                {
                    "type_id": 2, "name": "ATP", "year": 2026,
                    "week": 30, "gender": "men",
                    "competitor_rankings": [
                        {
                            "rank": 1, "movement": 0, "points": 1000,
                            "competitions_played": 12,
                            "competitor": {
                                "id": "sr:competitor:1", "name": "Player, One",
                                "country": "Croatia", "country_code": "HRV",
                                "abbreviation": "ONE",
                            },
                        }
                    ],
                }
            ],
        },
    }
    data = transform_payloads(payloads, ingested_at=ingested_at)
    assert data.counts()["categories"] == 1
    assert data.counts()["competitions"] == 1
    assert data.counts()["complexes"] == 1
    assert data.counts()["venues"] == 1
    assert data.counts()["competitors"] == 1


def test_missing_country_code_normalized(ingested_at):
    data = transform_payloads(
        {
            "doubles_rankings": {
                "rankings": [
                    {
                        "type_id": 2, "name": "WTA", "year": 2026,
                        "week": 30, "gender": "women",
                        "competitor_rankings": [
                            {
                                "rank": "7", "movement": None,
                                "points": "500", "competitions_played": "8",
                                "competitor": {
                                    "id": "sr:competitor:2",
                                    "name": "Player, Two",
                                    "country": "Neutral",
                                },
                            }
                        ],
                    }
                ]
            }
        },
        ingested_at=ingested_at,
    )
    assert data.competitors[0]["country_code"] == "UNK"
    assert data.competitor_rankings[0]["movement"] == 0
    assert data.competitor_rankings[0]["rank"] == 7


def test_empty_payload():
    data = transform_payloads({})
    assert data.counts()["categories"] == 0
    assert data.counts()["competitions"] == 0


def test_competition_without_category(ingested_at):
    cats, comps = transform_competitions(
        {"competitions": [{"id": "sr:comp:1", "name": "Test"}]},
        ingested_at=ingested_at,
    )
    assert len(comps) == 1
    assert comps[0]["category_id"] == "sr:category:unknown"


def test_competition_missing_id(ingested_at):
    cats, comps = transform_competitions(
        {"competitions": [{"name": "No ID comp"}]},
        ingested_at=ingested_at,
    )
    assert len(comps) == 0


def test_transformed_data_counts():
    data = TransformedData()
    counts = data.counts()
    assert all(v == 0 for v in counts.values())
