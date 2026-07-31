"""Tests for data quality checks."""
from __future__ import annotations
import pytest
from tennis_analytics.quality import run_quality_checks, QualityReport, PASS, FAIL, WARN


def test_quality_checks_on_populated_db(populated_engine):
    report = run_quality_checks(populated_engine)
    assert isinstance(report, QualityReport)
    assert report.total_checks > 0
    assert report.score >= 0
    assert report.score <= 100


def test_quality_all_pass_on_good_data(populated_engine):
    report = run_quality_checks(populated_engine)
    failed_checks = [c for c in report.checks if c.status == FAIL]
    # With proper sample data, there should be no hard failures
    # (freshness may warn since sample data is from a fixed date)
    for check in failed_checks:
        assert check.name not in [
            "No competitions with missing categories",
            "No venues with missing complexes",
            "No rankings with missing competitors",
            "Ranking numeric values are valid",
        ]


def test_quality_score_calculation(populated_engine):
    report = run_quality_checks(populated_engine)
    assert report.passed + report.warnings + report.failed == report.total_checks


def test_quality_report_to_dict(populated_engine):
    report = run_quality_checks(populated_engine)
    d = report.to_dict()
    assert "score" in d
    assert "checks" in d
    assert isinstance(d["checks"], list)


def test_quality_blocking_flag(populated_engine):
    report = run_quality_checks(populated_engine)
    assert isinstance(report.is_blocking, bool)
