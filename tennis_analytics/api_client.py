"""Sportradar Tennis API client with retry and rate-limit handling."""

from __future__ import annotations

import time
from dataclasses import dataclass
import logging
from typing import Any
from contextlib import contextmanager

import requests

from tennis_analytics.config import Settings
from tennis_analytics.exceptions import DataRefreshError


ENDPOINTS: dict[str, str] = {
    "competitions": "competitions.json",
    "complexes": "complexes.json",
    "doubles_rankings": "double_competitors_rankings.json",
}


logger = logging.getLogger(__name__)


class SportradarAPIError(DataRefreshError):
    """Raised when the Sportradar API request cannot be completed."""


@dataclass(frozen=True)
class APIResponse:
    """A parsed API response plus lightweight request metadata."""

    endpoint: str
    url: str
    status_code: int
    payload: dict[str, Any]


class SportradarTennisClient:
    """Small client for Sportradar Tennis v3 reference endpoints."""

    def __init__(self, settings: Settings) -> None:
        if not settings.api_key:
            raise ValueError("A Sportradar API key is required for API requests.")

        self.settings = settings
        self.base_url = (
            "https://api.sportradar.com/tennis/"
            f"{settings.access_level}/v3/{settings.language}"
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "accept": "application/json",
                "x-api-key": settings.api_key,
                "user-agent": "sport-radar-tennis-analytics/1.0",
            }
        )

    def fetch(self, endpoint: str) -> APIResponse:
        """Fetch and parse one named endpoint."""

        if endpoint not in ENDPOINTS:
            valid = ", ".join(sorted(ENDPOINTS))
            raise ValueError(f"Unknown endpoint '{endpoint}'. Valid endpoints: {valid}")

        url = f"{self.base_url}/{ENDPOINTS[endpoint]}"
        last_error: Exception | None = None

        for attempt in range(self.settings.max_retries + 1):
            try:
                logger.info("Fetching Sportradar endpoint '%s' (attempt %s)", endpoint, attempt + 1)
                start_time = time.time()
                response = self.session.get(url, timeout=self.settings.timeout_seconds)
                if response.status_code == 429 or 500 <= response.status_code < 600:
                    logger.warning(
                        "Retryable Sportradar response for '%s': HTTP %s",
                        endpoint,
                        response.status_code,
                    )
                    self._sleep_before_retry(response, attempt)
                    continue
                response.raise_for_status()
                elapsed = time.time() - start_time
                logger.info("Successfully fetched '%s' in %.2fs", endpoint, elapsed)
                return APIResponse(
                    endpoint=endpoint,
                    url=url,
                    status_code=response.status_code,
                    payload=response.json(),
                )
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                logger.warning("Sportradar request failed for '%s': %s", endpoint, exc)
                if attempt >= self.settings.max_retries:
                    break
                time.sleep(min(2**attempt, 30))

        raise SportradarAPIError(
            f"Failed to fetch '{endpoint}' from Sportradar after "
            f"{self.settings.max_retries + 1} attempts: {last_error}"
        )

    def fetch_all(self) -> dict[str, APIResponse]:
        """Fetch every endpoint required by the project brief."""

        return {endpoint: self.fetch(endpoint) for endpoint in ENDPOINTS}

    def health_check(self) -> bool:
        """Lightweight request to verify the API key is valid."""
        try:
            self.fetch("competitions")
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the underlying session."""
        self.session.close()

    def __enter__(self) -> SportradarTennisClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    @staticmethod
    def _sleep_before_retry(response: requests.Response, attempt: int) -> None:
        retry_after = response.headers.get("retry-after")
        if retry_after and retry_after.isdigit():
            sleep_seconds = int(retry_after)
        else:
            sleep_seconds = min(2**attempt, 30)
        time.sleep(sleep_seconds)
