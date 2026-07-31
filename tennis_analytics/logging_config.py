"""Logging helpers with secret redaction."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
from logging.handlers import RotatingFileHandler
import json


SECRET_PATTERNS = (
    re.compile(r"(x-api-key['\"]?\s*[:=]\s*['\"]?)([^'\"\s,}]+)", re.IGNORECASE),
    re.compile(r"(api[_-]?key['\"]?\s*[:=]\s*['\"]?)([^'\"\s,}]+)", re.IGNORECASE),
    re.compile(r"([?&]api_key=)([^&\s]+)", re.IGNORECASE),
)


class RedactingFilter(logging.Filter):
    """Remove API keys and credential-like tokens from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_secret(record.getMessage())
        record.args = ()
        return True


def redact_secret(value: Any) -> str:
    """Return a printable string with common API-key patterns masked."""

    text = str(value)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(r"\1***", text)
    return text


def configure_logging(log_dir: Path | None = None, *, level: int = logging.INFO) -> None:
    """Configure console and optional file logging once per process."""

    root = logging.getLogger()
    if any(getattr(handler, "_tennis_analytics", False) for handler in root.handlers):
        return

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(RedactingFilter())
    console._tennis_analytics = True  # type: ignore[attr-defined]
    root.addHandler(console)

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_dir / "tennis_analytics.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RedactingFilter())
        file_handler._tennis_analytics = True  # type: ignore[attr-defined]
        root.addHandler(file_handler)

    root.setLevel(level)


def configure_json_logging(log_dir: Path | None = None, *, level: int = logging.INFO) -> None:
    """Configure JSON-structured file logging."""
    
    root = logging.getLogger()
    if any(getattr(handler, "_tennis_analytics_json", False) for handler in root.handlers):
        return

    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            msg = record.getMessage()
            if hasattr(record, "msg") and not isinstance(record.msg, str):
                pass
            
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": msg
            }
            return json.dumps(log_record)

    console = logging.StreamHandler()
    console.setFormatter(JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ"))
    console.addFilter(RedactingFilter())
    console._tennis_analytics_json = True # type: ignore[attr-defined]
    root.addHandler(console)

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_dir / "tennis_analytics.json.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter(datefmt="%Y-%m-%dT%H:%M:%SZ"))
        file_handler.addFilter(RedactingFilter())
        file_handler._tennis_analytics_json = True  # type: ignore[attr-defined]
        root.addHandler(file_handler)

    root.setLevel(level)

