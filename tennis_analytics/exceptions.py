"""Project-specific exception hierarchy with structured error context."""

from __future__ import annotations


class TennisAnalyticsError(Exception):
    """Base class for recoverable project errors."""

    def __init__(self, message: str, *, context: dict | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class ConfigurationError(TennisAnalyticsError):
    """Raised when required runtime configuration is missing or invalid."""


class DataRefreshError(TennisAnalyticsError):
    """Raised when the data refresh workflow cannot complete safely."""


class DataQualityError(TennisAnalyticsError):
    """Raised when data quality checks fail in a blocking context."""


class QueryExecutionError(TennisAnalyticsError):
    """Raised when a dashboard or analysis query cannot be executed."""


class TransformationError(TennisAnalyticsError):
    """Raised when data transformation encounters invalid or unexpected input."""


class PipelineError(TennisAnalyticsError):
    """Raised when a pipeline step fails with step-level context."""

    def __init__(
        self,
        message: str,
        *,
        step: str = "unknown",
        context: dict | None = None,
    ) -> None:
        super().__init__(message, context=context)
        self.step = step
