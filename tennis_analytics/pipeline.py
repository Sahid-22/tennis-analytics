"""End-to-end API extraction, transform, load, and export pipeline."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tennis_analytics.api_client import APIResponse, SportradarTennisClient, ENDPOINTS
from tennis_analytics.config import Settings
from tennis_analytics.database import (
    create_database_engine,
    export_tables_to_csv,
    get_table_counts,
    replace_all_data,
)
from tennis_analytics.quality import QualityReport, run_quality_checks, write_quality_report
from tennis_analytics.transformers import TransformedData, transform_payloads


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineStepResult:
    step_name: str
    success: bool
    duration_seconds: float
    record_count: int
    error: str | None


@dataclass(frozen=True)
class RefreshResult:
    """Summary of a completed data refresh."""

    table_counts: dict[str, int]
    raw_files: dict[str, Path]
    csv_files: dict[str, Path]
    quality_report: QualityReport
    quality_files: dict[str, Path]
    database_url: str
    step_results: tuple[PipelineStepResult, ...] = ()


def run_refresh(
    settings: Settings,
    *,
    save_raw: bool = True,
    export_csv: bool = True,
) -> RefreshResult:
    """Run the full ETL workflow required by the project brief."""

    fetched_at = datetime.now(timezone.utc)
    logger.info("Starting Sportradar tennis data refresh")
    client = SportradarTennisClient(settings)
    
    responses = {}
    step_results_list = []
    
    for endpoint in ENDPOINTS:
        start_t = time.time()
        try:
            resp = client.fetch(endpoint)
            responses[endpoint] = resp
            step_results_list.append(PipelineStepResult(
                step_name=f"fetch_{endpoint}",
                success=True,
                duration_seconds=time.time() - start_t,
                record_count=1,
                error=None
            ))
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", endpoint, exc)
            step_results_list.append(PipelineStepResult(
                step_name=f"fetch_{endpoint}",
                success=False,
                duration_seconds=time.time() - start_t,
                record_count=0,
                error=str(exc)
            ))
            
    if not responses:
        raise RuntimeError("All fetch operations failed.")

    payloads = {endpoint: response.payload for endpoint, response in responses.items()}

    t_start = time.time()
    try:
        data = transform_payloads(payloads, ingested_at=fetched_at)
        data.api_sync_log = _build_sync_log(responses, data, fetched_at)
        step_results_list.append(PipelineStepResult("transform", True, time.time() - t_start, 0, None))
    except Exception as exc:
        step_results_list.append(PipelineStepResult("transform", False, time.time() - t_start, 0, str(exc)))
        # In partial recovery, we log but maybe we want to continue if possible. But data is needed.
        logger.error("Transform failed: %s", exc)
        data = None

    raw_files = _save_raw_payloads(responses, settings.raw_dir) if save_raw else {}

    engine = create_database_engine(settings.database_url)
    
    l_start = time.time()
    if data is not None:
        try:
            replace_all_data(engine, data)
            step_results_list.append(PipelineStepResult("load", True, time.time() - l_start, 0, None))
        except Exception as exc:
            step_results_list.append(PipelineStepResult("load", False, time.time() - l_start, 0, str(exc)))
            logger.error("Load failed: %s", exc)

    table_counts = get_table_counts(engine)
    csv_files = export_tables_to_csv(engine, settings.processed_dir) if export_csv else {}
    
    q_start = time.time()
    try:
        quality_report = run_quality_checks(
            engine,
            freshness_warning_days=settings.quality_warning_days,
        )
        quality_files = write_quality_report(quality_report, settings.report_dir)
        step_results_list.append(PipelineStepResult("quality", True, time.time() - q_start, 0, None))
        
        logger.info(
            "Refresh complete with quality score %s/100 (%s failed checks)",
            quality_report.score,
            quality_report.failed,
        )
    except Exception as exc:
        step_results_list.append(PipelineStepResult("quality", False, time.time() - q_start, 0, str(exc)))
        logger.error("Quality checks failed: %s", exc)
        # Create a dummy quality report
        from tennis_analytics.quality import QualityReport
        quality_report = QualityReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            score=0,
            total_checks=0,
            passed=0,
            warnings=0,
            failed=0,
            checks=[]
        )
        quality_files = {}

    return RefreshResult(
        table_counts=table_counts,
        raw_files=raw_files,
        csv_files=csv_files,
        quality_report=quality_report,
        quality_files=quality_files,
        database_url=settings.database_url,
        step_results=tuple(step_results_list),
    )


def _save_raw_payloads(
    responses: dict[str, APIResponse],
    raw_dir: Path,
) -> dict[str, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    saved: dict[str, Path] = {}

    for endpoint, response in responses.items():
        snapshot_path = raw_dir / f"{endpoint}_{timestamp}.json"
        latest_path = raw_dir / f"{endpoint}_latest.json"
        payload_text = json.dumps(response.payload, ensure_ascii=False, indent=2)
        snapshot_path.write_text(payload_text, encoding="utf-8")
        latest_path.write_text(payload_text, encoding="utf-8")
        saved[endpoint] = snapshot_path

    return saved


def _build_sync_log(
    responses: dict[str, APIResponse],
    data: TransformedData,
    fetched_at: datetime,
) -> list[dict[str, Any]]:
    row_counts = {
        "competitions": len(data.competitions),
        "complexes": len(data.complexes),
        "doubles_rankings": len(data.competitor_rankings),
    }
    rows: list[dict[str, Any]] = []

    for endpoint, response in responses.items():
        payload_bytes = json.dumps(
            response.payload, sort_keys=True, ensure_ascii=True
        ).encode("utf-8")
        rows.append(
            {
                "endpoint": endpoint,
                "source_generated_at": response.payload.get("generated_at"),
                "fetched_at": fetched_at,
                "status_code": response.status_code,
                "row_count": row_counts.get(endpoint, 0),
                "payload_sha256": hashlib.sha256(payload_bytes).hexdigest(),
            }
        )

    return rows
