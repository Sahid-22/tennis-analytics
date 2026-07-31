"""Configuration helpers for the tennis analytics project."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from tennis_analytics.exceptions import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SQLITE_PATH = DEFAULT_DATA_DIR / "tennis_analytics.db"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    api_key: str | None
    database_url: str
    access_level: str
    language: str
    timeout_seconds: int
    max_retries: int
    data_dir: Path
    raw_dir: Path
    processed_dir: Path
    report_dir: Path
    log_dir: Path
    quality_warning_days: int
    dashboard_theme: str
    auto_refresh_minutes: int
    export_enabled: bool


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def _normalise_database_url(value: str | None) -> str:
    """Return an absolute SQLAlchemy URL for local SQLite defaults."""

    if not value:
        return _sqlite_url(DEFAULT_SQLITE_PATH)

    if value.startswith("sqlite:///"):
        raw_path = value.removeprefix("sqlite:///")
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / raw_path
        return _sqlite_url(candidate)

    return value


def get_settings(
    *,
    api_key_override: str | None = None,
    require_api_key: bool = False,
) -> Settings:
    """Load settings from .env/environment with optional API-key override."""

    load_dotenv(PROJECT_ROOT / ".env")

    data_dir = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR)))
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    report_dir = Path(os.getenv("REPORT_DIR", str(DEFAULT_REPORT_DIR)))
    if not report_dir.is_absolute():
        report_dir = PROJECT_ROOT / report_dir

    log_dir = Path(os.getenv("LOG_DIR", str(DEFAULT_LOG_DIR)))
    if not log_dir.is_absolute():
        log_dir = PROJECT_ROOT / log_dir

    api_key = api_key_override or os.getenv("SPORTRADAR_API_KEY")
    if require_api_key and not api_key:
        raise ConfigurationError(
            "SPORTRADAR_API_KEY is required. Set it in the environment, .env, "
            "or pass it through the Streamlit refresh form."
        )

    timeout_seconds = _positive_int("SPORTRADAR_TIMEOUT_SECONDS", default=30)
    max_retries = _non_negative_int("SPORTRADAR_MAX_RETRIES", default=3)
    quality_warning_days = _positive_int("QUALITY_WARNING_DAYS", default=7)

    return Settings(
        api_key=api_key,
        database_url=_normalise_database_url(os.getenv("DATABASE_URL")),
        access_level=os.getenv("SPORTRADAR_ACCESS_LEVEL", "trial"),
        language=os.getenv("SPORTRADAR_LANGUAGE", "en"),
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        processed_dir=data_dir / "processed",
        report_dir=report_dir,
        log_dir=log_dir,
        quality_warning_days=quality_warning_days,
        dashboard_theme=os.getenv("DASHBOARD_THEME", "dark"),
        auto_refresh_minutes=int(os.getenv("AUTO_REFRESH_MINUTES", "0")),
        export_enabled=os.getenv("EXPORT_ENABLED", "true").lower() in ("true", "1", "yes"),
    )


def _positive_int(name: str, *, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be greater than zero.")
    return value


def _non_negative_int(name: str, *, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc
    if value < 0:
        raise ConfigurationError(f"{name} cannot be negative.")
    return value
