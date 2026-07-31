"""Tests for database schema and persistence."""
from __future__ import annotations
import pytest
import pandas as pd
from tennis_analytics.database import (
    create_database_engine,
    get_table_counts,
    query_dataframe,
    replace_all_data,
    TABLES_IN_LOAD_ORDER,
)


def test_schema_creation(in_memory_engine):
    counts = get_table_counts(in_memory_engine)
    assert len(counts) == len(TABLES_IN_LOAD_ORDER)
    for table in TABLES_IN_LOAD_ORDER:
        assert table.name in counts
        assert counts[table.name] == 0


def test_replace_all_data_loads(populated_engine):
    counts = get_table_counts(populated_engine)
    assert counts["categories"] == 2
    assert counts["competitions"] == 2
    assert counts["complexes"] == 1
    assert counts["venues"] == 1
    assert counts["competitors"] == 2
    assert counts["competitor_rankings"] == 2
    assert counts["api_sync_log"] == 3


def test_query_dataframe_returns_pandas(populated_engine):
    df = query_dataframe(populated_engine, "SELECT * FROM categories")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_join_query(populated_engine):
    df = query_dataframe(
        populated_engine,
        """
        SELECT cmp.name, cr.rank, cr.points
        FROM competitor_rankings AS cr
        INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
        ORDER BY cr.rank
        """,
    )
    assert df.iloc[0]["name"] == "Player, One"
    assert int(df.iloc[0]["points"]) == 8000


def test_replace_is_idempotent(in_memory_engine, sample_data):
    replace_all_data(in_memory_engine, sample_data)
    replace_all_data(in_memory_engine, sample_data)
    counts = get_table_counts(in_memory_engine)
    assert counts["categories"] == 2  # Not doubled


def test_foreign_key_integrity(populated_engine):
    df = query_dataframe(
        populated_engine,
        """
        SELECT c.competition_name, cat.category_name
        FROM competitions AS c
        INNER JOIN categories AS cat ON c.category_id = cat.category_id
        """,
    )
    assert len(df) == 2
