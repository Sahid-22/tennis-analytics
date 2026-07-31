"""Transform Sportradar nested JSON payloads into relational rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass
class TransformedData:
    """Container for all normalized table rows produced by the ETL step."""

    categories: list[dict[str, Any]] = field(default_factory=list)
    competitions: list[dict[str, Any]] = field(default_factory=list)
    complexes: list[dict[str, Any]] = field(default_factory=list)
    venues: list[dict[str, Any]] = field(default_factory=list)
    competitors: list[dict[str, Any]] = field(default_factory=list)
    competitor_rankings: list[dict[str, Any]] = field(default_factory=list)
    api_sync_log: list[dict[str, Any]] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "categories": len(self.categories),
            "competitions": len(self.competitions),
            "complexes": len(self.complexes),
            "venues": len(self.venues),
            "competitors": len(self.competitors),
            "competitor_rankings": len(self.competitor_rankings),
            "api_sync_log": len(self.api_sync_log),
        }


def transform_payloads(
    payloads: Mapping[str, dict[str, Any]],
    *,
    ingested_at: datetime | None = None,
) -> TransformedData:
    """Transform all project payloads into normalized row dictionaries."""

    ingested_at = ingested_at or datetime.now(timezone.utc)
    result = TransformedData()

    if "competitions" in payloads:
        categories, competitions = transform_competitions(
            payloads["competitions"], ingested_at=ingested_at
        )
        result.categories = categories
        result.competitions = competitions

    if "complexes" in payloads:
        complexes, venues = transform_complexes(
            payloads["complexes"], ingested_at=ingested_at
        )
        result.complexes = complexes
        result.venues = venues

    if "doubles_rankings" in payloads:
        competitors, rankings = transform_doubles_rankings(
            payloads["doubles_rankings"], ingested_at=ingested_at
        )
        result.competitors = competitors
        result.competitor_rankings = rankings

    return result


def transform_competitions(
    payload: Mapping[str, Any],
    *,
    ingested_at: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Flatten competition and category records."""

    categories: dict[str, dict[str, Any]] = {}
    competitions: dict[str, dict[str, Any]] = {}

    for item in payload.get("competitions", []):
        competition_id = _clean_text(item.get("id"))
        if not competition_id:
            continue

        category = item.get("category") or {}
        category_id = _clean_text(category.get("id")) or "sr:category:unknown"
        categories[category_id] = {
            "category_id": category_id,
            "category_name": _clean_text(category.get("name")) or "Unknown",
            "ingested_at": ingested_at,
        }

        competitions[competition_id] = {
            "competition_id": competition_id,
            "competition_name": _clean_text(item.get("name")) or "Unknown",
            "parent_id": _clean_text(item.get("parent_id")),
            "type": _clean_text(item.get("type")) or "unknown",
            "gender": _clean_text(item.get("gender")) or "unknown",
            "level": _clean_text(item.get("level")),
            "category_id": category_id,
            "ingested_at": ingested_at,
        }

    return list(categories.values()), list(competitions.values())


def transform_complexes(
    payload: Mapping[str, Any],
    *,
    ingested_at: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Flatten complex and venue records."""

    complexes: dict[str, dict[str, Any]] = {}
    venues: dict[str, dict[str, Any]] = {}

    for item in payload.get("complexes", []):
        complex_id = _clean_text(item.get("id"))
        if not complex_id:
            continue

        complexes[complex_id] = {
            "complex_id": complex_id,
            "complex_name": _clean_text(item.get("name")) or "Unknown",
            "ingested_at": ingested_at,
        }

        for venue in item.get("venues", []) or []:
            venue_id = _clean_text(venue.get("id"))
            if not venue_id:
                continue

            venues[venue_id] = {
                "venue_id": venue_id,
                "venue_name": _clean_text(venue.get("name")) or "Unknown",
                "city_name": _clean_text(venue.get("city_name")) or "Unknown",
                "city_id": _clean_text(venue.get("city_id")),
                "country_name": _clean_text(venue.get("country_name")) or "Unknown",
                "country_code": _country_code(venue.get("country_code")),
                "timezone": _clean_text(venue.get("timezone")) or "Unknown",
                "complex_id": complex_id,
                "ingested_at": ingested_at,
            }

    return list(complexes.values()), list(venues.values())


def transform_doubles_rankings(
    payload: Mapping[str, Any],
    *,
    ingested_at: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Flatten doubles competitor rankings and competitor dimensions."""

    competitors: dict[str, dict[str, Any]] = {}
    rankings: list[dict[str, Any]] = []
    source_generated_at = _clean_text(payload.get("generated_at"))

    for ranking_group in payload.get("rankings", []) or []:
        ranking_name = _clean_text(ranking_group.get("name")) or "Unknown"
        ranking_type_id = _to_int(ranking_group.get("type_id"))
        ranking_year = _to_int(ranking_group.get("year"))
        ranking_week = _to_int(ranking_group.get("week"))
        ranking_gender = _clean_text(ranking_group.get("gender")) or "unknown"

        for item in ranking_group.get("competitor_rankings", []) or []:
            competitor = item.get("competitor") or {}
            competitor_id = _clean_text(competitor.get("id"))
            if not competitor_id:
                continue

            competitors[competitor_id] = {
                "competitor_id": competitor_id,
                "name": _clean_text(competitor.get("name")) or "Unknown",
                "country": _clean_text(competitor.get("country")) or "Unknown",
                "country_code": _country_code(competitor.get("country_code")),
                "abbreviation": _clean_text(competitor.get("abbreviation")) or "UNK",
                "ingested_at": ingested_at,
            }

            rankings.append(
                {
                    "rank": _to_int(item.get("rank")),
                    "movement": _to_int(item.get("movement")),
                    "points": _to_int(item.get("points")),
                    "competitions_played": _to_int(item.get("competitions_played")),
                    "competitor_id": competitor_id,
                    "ranking_type_id": ranking_type_id,
                    "ranking_name": ranking_name,
                    "ranking_year": ranking_year,
                    "ranking_week": ranking_week,
                    "ranking_gender": ranking_gender,
                    "source_generated_at": source_generated_at,
                    "ingested_at": ingested_at,
                }
            )

    return list(competitors.values()), rankings


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _country_code(value: Any) -> str:
    code = _clean_text(value)
    if not code:
        return "UNK"
    return code.upper()[:3]


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default

