"""Tests for SQL query catalog."""
from __future__ import annotations
import pytest
import pandas as pd
from tennis_analytics.queries import REQUIRED_QUERIES, EXTRA_INSIGHT_QUERIES, QuerySpec
from tennis_analytics.database import query_dataframe


def test_required_queries_structure():
    assert len(REQUIRED_QUERIES) == 3
    for section, queries in REQUIRED_QUERIES.items():
        assert isinstance(queries, list)
        for q in queries:
            assert isinstance(q, QuerySpec)
            assert q.title
            assert q.sql.strip()


def test_extra_insight_queries_structure():
    assert len(EXTRA_INSIGHT_QUERIES) >= 3
    for title, spec in EXTRA_INSIGHT_QUERIES.items():
        assert isinstance(spec, QuerySpec)
        assert spec.sql.strip()


def test_all_required_queries_execute(populated_engine):
    for section, queries in REQUIRED_QUERIES.items():
        for spec in queries:
            params = spec.default_params or {}
            df = query_dataframe(populated_engine, spec.sql, params)
            assert isinstance(df, pd.DataFrame)


def test_extra_queries_execute(populated_engine):
    for title, spec in EXTRA_INSIGHT_QUERIES.items():
        df = query_dataframe(populated_engine, spec.sql)
        assert isinstance(df, pd.DataFrame)
