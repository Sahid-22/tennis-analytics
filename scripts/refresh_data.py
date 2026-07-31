"""Refresh the local analytics database from Sportradar."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tennis_analytics.config import get_settings  # noqa: E402
from tennis_analytics.logging_config import configure_logging  # noqa: E402
from tennis_analytics.pipeline import run_refresh  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Sportradar tennis data and populate the analytics database."
    )
    parser.add_argument(
        "--no-raw",
        action="store_true",
        help="Do not write raw JSON snapshots to data/raw.",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Do not export processed CSV tables to data/processed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings(require_api_key=True)
    configure_logging(settings.log_dir)
    result = run_refresh(
        settings,
        save_raw=not args.no_raw,
        export_csv=not args.no_csv,
    )

    print("Refresh complete")
    print(f"Database: {result.database_url}")
    for table, count in result.table_counts.items():
        print(f"{table}: {count}")
    if result.raw_files:
        print("Raw snapshots:")
        for endpoint, path in result.raw_files.items():
            print(f"  {endpoint}: {path}")
    if result.csv_files:
        print("CSV exports:")
        for table, path in result.csv_files.items():
            print(f"  {table}: {path}")
    print(
        "Data quality: "
        f"{result.quality_report.score}/100 "
        f"({result.quality_report.failed} failed, "
        f"{result.quality_report.warnings} warnings)"
    )
    for report_type, path in result.quality_files.items():
        print(f"{report_type.title()} report: {path}")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
