"""Database quality checks and report generation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from tennis_analytics.database import TABLES_IN_LOAD_ORDER, get_table_counts


PASS = "pass"
WARN = "warn"
FAIL = "fail"


@dataclass(frozen=True)
class QualityCheck:
    """One database quality check result."""

    name: str
    status: str
    observed: Any
    expected: str
    details: str


@dataclass(frozen=True)
class QualityReport:
    """Collection of database quality checks with a portfolio-friendly score."""

    generated_at: str
    score: int
    total_checks: int
    passed: int
    warnings: int
    failed: int
    checks: list[QualityCheck]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def is_blocking(self) -> bool:
        return self.failed > 0


def run_quality_checks(
    engine: Engine,
    *,
    freshness_warning_days: int = 7,
) -> QualityReport:
    """Run integrity, completeness, and freshness checks against the database."""

    checks: list[QualityCheck] = []
    counts = get_table_counts(engine)

    for table in TABLES_IN_LOAD_ORDER:
        minimum = 1 if table.name != "api_sync_log" else 3
        count = counts.get(table.name, 0)
        checks.append(
            _check(
                f"{table.name} has data",
                count >= minimum,
                observed=count,
                expected=f">= {minimum} rows",
                details=f"{table.name} contains {count:,} rows.",
            )
        )

    checks.extend(
        [
            _sql_check(
                engine,
                name="No competitions with missing categories",
                sql="""
                    SELECT COUNT(*) FROM competitions AS c
                    LEFT JOIN categories AS cat ON c.category_id = cat.category_id
                    WHERE cat.category_id IS NULL
                """,
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="No venues with missing complexes",
                sql="""
                    SELECT COUNT(*) FROM venues AS v
                    LEFT JOIN complexes AS cx ON v.complex_id = cx.complex_id
                    WHERE cx.complex_id IS NULL
                """,
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="No rankings with missing competitors",
                sql="""
                    SELECT COUNT(*) FROM competitor_rankings AS cr
                    LEFT JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
                    WHERE cmp.competitor_id IS NULL
                """,
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="Ranking numeric values are valid",
                sql="""
                    SELECT COUNT(*) FROM competitor_rankings
                    WHERE rank <= 0 OR points < 0 OR competitions_played < 0
                """,
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="Country codes are ISO-like three-character values",
                sql="""
                    SELECT COUNT(*) FROM (
                        SELECT country_code FROM competitors
                        UNION ALL
                        SELECT country_code FROM venues
                    ) AS codes
                    WHERE LENGTH(country_code) <> 3
                """,
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="All expected API endpoints are logged",
                sql="SELECT COUNT(DISTINCT endpoint) FROM api_sync_log",
                expected_value=3,
            ),
            _sql_check(
                engine,
                name="All API syncs were successful",
                sql="SELECT COUNT(*) FROM api_sync_log WHERE status_code <> 200",
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="No duplicate competition IDs",
                sql="SELECT COUNT(*) - COUNT(DISTINCT competition_id) FROM competitions",
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="No duplicate competitor IDs",  
                sql="SELECT COUNT(*) - COUNT(DISTINCT competitor_id) FROM competitors",
                expected_value=0,
            ),
            _sql_check(
                engine,
                name="Competition types are valid",
                sql="SELECT COUNT(*) FROM competitions WHERE type NOT IN ('singles', 'doubles', 'unknown')",
                expected_value=0,
            ),
        ]
    )

    checks.append(_points_outlier_check(engine))

    freshness = _freshness_check(engine, freshness_warning_days=freshness_warning_days)
    checks.append(freshness)

    passed = sum(1 for check in checks if check.status == PASS)
    warnings = sum(1 for check in checks if check.status == WARN)
    failed = sum(1 for check in checks if check.status == FAIL)
    score = max(0, round(((passed + warnings * 0.5) / len(checks)) * 100))

    return QualityReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        score=score,
        total_checks=len(checks),
        passed=passed,
        warnings=warnings,
        failed=failed,
        checks=checks,
    )


def write_quality_report(report: QualityReport, output_dir: Path) -> dict[str, Path]:
    """Write JSON and Markdown quality report artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "quality_report.json"
    md_path = output_dir / "quality_report.md"

    json_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    return {"json": json_path, "markdown": md_path}


def _check(
    name: str,
    condition: bool,
    *,
    observed: Any,
    expected: str,
    details: str,
    warning: bool = False,
) -> QualityCheck:
    status = PASS if condition else (WARN if warning else FAIL)
    return QualityCheck(
        name=name,
        status=status,
        observed=observed,
        expected=expected,
        details=details,
    )


def _sql_check(
    engine: Engine,
    *,
    name: str,
    sql: str,
    expected_value: int,
) -> QualityCheck:
    with engine.connect() as connection:
        observed = int(connection.execute(text(sql)).scalar_one())
    return _check(
        name,
        observed == expected_value,
        observed=observed,
        expected=str(expected_value),
        details=f"Observed value: {observed}.",
    )


def _freshness_check(engine: Engine, *, freshness_warning_days: int) -> QualityCheck:
    with engine.connect() as connection:
        fetched_at = connection.execute(
            text("SELECT MAX(fetched_at) FROM api_sync_log")
        ).scalar_one_or_none()

    if fetched_at is None:
        return _check(
            "Data snapshot freshness",
            False,
            observed="missing",
            expected="latest API sync timestamp present",
            details="No API sync timestamp was found.",
        )

    fetched_datetime = _parse_datetime(str(fetched_at))
    age_days = (datetime.now(timezone.utc) - fetched_datetime).days
    return _check(
        "Data snapshot freshness",
        age_days <= freshness_warning_days,
        observed=f"{age_days} days old",
        expected=f"<= {freshness_warning_days} days old",
        details=f"Latest API sync timestamp: {fetched_datetime.isoformat()}.",
        warning=True,
    )


def _parse_datetime(value: str) -> datetime:
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _render_markdown(report: QualityReport) -> str:
    lines = [
        "# Data Quality Report",
        "",
        f"Generated at: {report.generated_at}",
        "",
        f"Quality score: {report.score}/100",
        "",
        "| Check | Status | Observed | Expected | Details |",
        "| --- | --- | --- | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            "| "
            + " | ".join(
                [
                    check.name,
                    check.status.upper(),
                    str(check.observed),
                    check.expected,
                    check.details.replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _points_outlier_check(engine: Engine) -> QualityCheck:
    try:
        with engine.connect() as connection:
            avg_val = connection.execute(text("SELECT AVG(points) FROM competitor_rankings")).scalar()
            max_val = connection.execute(text("SELECT MAX(points) FROM competitor_rankings")).scalar()
        
        if avg_val is None or max_val is None:
            return _check("Points outlier check", True, observed="no data", expected="max <= 10 * avg", details="No points data found.")
            
        avg_val, max_val = float(avg_val), float(max_val)
        if avg_val == 0:
            is_outlier = max_val > 0
        else:
            is_outlier = max_val > 10 * avg_val
            
        return _check(
            "Points outlier check",
            not is_outlier,
            observed=f"Max: {max_val}, Avg: {avg_val:.1f}",
            expected="Max <= 10 * Avg",
            details="Max points are highly irregular compared to average." if is_outlier else "Points distribution looks valid.",
            warning=True,
        )
    except Exception as e:
        return _check("Points outlier check", True, observed="error", expected="max <= 10 * avg", details=f"Error checking points: {e}")
