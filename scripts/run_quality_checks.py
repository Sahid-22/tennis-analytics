"""Run database quality checks and write report artifacts."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tennis_analytics.config import get_settings  # noqa: E402
from tennis_analytics.database import create_database_engine  # noqa: E402
from tennis_analytics.logging_config import configure_logging  # noqa: E402
from tennis_analytics.quality import run_quality_checks, write_quality_report  # noqa: E402


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_dir)
    engine = create_database_engine(settings.database_url)
    report = run_quality_checks(
        engine,
        freshness_warning_days=settings.quality_warning_days,
    )
    files = write_quality_report(report, settings.report_dir)

    print(f"Quality score: {report.score}/100")
    print(f"Passed: {report.passed}")
    print(f"Warnings: {report.warnings}")
    print(f"Failed: {report.failed}")
    for report_type, path in files.items():
        print(f"{report_type.title()} report: {path}")
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
