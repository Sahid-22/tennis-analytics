"""Database schema and persistence helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import logging

import pandas as pd
from sqlalchemy import (
    CHAR,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    event,
    func,
    insert,
    select,
    text,
)
from sqlalchemy.engine import Engine

from tennis_analytics.transformers import TransformedData
from tennis_analytics.exceptions import QueryExecutionError


logger = logging.getLogger(__name__)


metadata = MetaData()

categories = Table(
    "categories",
    metadata,
    Column("category_id", String(50), primary_key=True),
    Column("category_name", String(100), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
)

competitions = Table(
    "competitions",
    metadata,
    Column("competition_id", String(50), primary_key=True),
    Column("competition_name", String(150), nullable=False),
    Column("parent_id", String(50), nullable=True),
    Column("type", String(20), nullable=False),
    Column("gender", String(10), nullable=False),
    Column("level", String(50), nullable=True),
    Column("category_id", String(50), ForeignKey("categories.category_id"), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    Index("idx_competitions_category_id", "category_id"),
    Index("idx_competitions_type_gender", "type", "gender"),
    Index("idx_competitions_parent_id", "parent_id"),
)

complexes = Table(
    "complexes",
    metadata,
    Column("complex_id", String(50), primary_key=True),
    Column("complex_name", String(100), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
)

venues = Table(
    "venues",
    metadata,
    Column("venue_id", String(50), primary_key=True),
    Column("venue_name", String(120), nullable=False),
    Column("city_name", String(100), nullable=False),
    Column("city_id", String(50), nullable=True),
    Column("country_name", String(100), nullable=False),
    Column("country_code", CHAR(3), nullable=False),
    Column("timezone", String(100), nullable=False),
    Column("complex_id", String(50), ForeignKey("complexes.complex_id"), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    Index("idx_venues_country_name", "country_name"),
    Index("idx_venues_complex_id", "complex_id"),
)

competitors = Table(
    "competitors",
    metadata,
    Column("competitor_id", String(50), primary_key=True),
    Column("name", String(120), nullable=False),
    Column("country", String(100), nullable=False),
    Column("country_code", CHAR(3), nullable=False),
    Column("abbreviation", String(10), nullable=False),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    Index("idx_competitors_country", "country"),
    Index("idx_competitors_name", "name"),
)

competitor_rankings = Table(
    "competitor_rankings",
    metadata,
    Column("rank_id", Integer, primary_key=True, autoincrement=True),
    Column("rank", Integer, nullable=False),
    Column("movement", Integer, nullable=False),
    Column("points", Integer, nullable=False),
    Column("competitions_played", Integer, nullable=False),
    Column(
        "competitor_id",
        String(50),
        ForeignKey("competitors.competitor_id"),
        nullable=False,
    ),
    Column("ranking_type_id", Integer, nullable=False),
    Column("ranking_name", String(50), nullable=False),
    Column("ranking_year", Integer, nullable=False),
    Column("ranking_week", Integer, nullable=False),
    Column("ranking_gender", String(10), nullable=False),
    Column("source_generated_at", String(40), nullable=True),
    Column("ingested_at", DateTime(timezone=True), nullable=False),
    Index("idx_rankings_rank_points", "rank", "points"),
    Index("idx_rankings_competitor_id", "competitor_id"),
    Index("idx_rankings_week", "ranking_year", "ranking_week", "ranking_name"),
)

api_sync_log = Table(
    "api_sync_log",
    metadata,
    Column("sync_id", Integer, primary_key=True, autoincrement=True),
    Column("endpoint", String(80), nullable=False),
    Column("source_generated_at", String(40), nullable=True),
    Column("fetched_at", DateTime(timezone=True), nullable=False),
    Column("status_code", Integer, nullable=False),
    Column("row_count", Integer, nullable=False),
    Column("payload_sha256", String(64), nullable=False),
    Index("idx_api_sync_log_endpoint", "endpoint"),
)

TABLES_IN_LOAD_ORDER: tuple[Table, ...] = (
    categories,
    competitions,
    complexes,
    venues,
    competitors,
    competitor_rankings,
    api_sync_log,
)

TABLES_IN_DELETE_ORDER: tuple[Table, ...] = tuple(reversed(TABLES_IN_LOAD_ORDER))


def create_database_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine and enable SQLite foreign keys."""

    engine = create_engine(database_url, future=True)
    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    return engine


def initialise_database(engine: Engine) -> None:
    metadata.create_all(engine)


def replace_all_data(engine: Engine, data: TransformedData) -> None:
    """Replace all analytical tables with a fresh API snapshot."""

    initialise_database(engine)
    rows_by_table: dict[str, list[dict[str, Any]]] = {
        "categories": data.categories,
        "competitions": data.competitions,
        "complexes": data.complexes,
        "venues": data.venues,
        "competitors": data.competitors,
        "competitor_rankings": data.competitor_rankings,
        "api_sync_log": data.api_sync_log,
    }

    with engine.begin() as connection:
        for table in TABLES_IN_DELETE_ORDER:
            connection.execute(table.delete())
        for table in TABLES_IN_LOAD_ORDER:
            rows = rows_by_table[table.name]
            if rows:
                connection.execute(insert(table), rows)
                logger.info("Loaded %s rows into %s", len(rows), table.name)


def get_table_counts(engine: Engine) -> dict[str, int]:
    """Return row counts for every project table."""

    initialise_database(engine)
    counts: dict[str, int] = {}
    with engine.connect() as connection:
        for table in TABLES_IN_LOAD_ORDER:
            counts[table.name] = int(
                connection.execute(select(func.count()).select_from(table)).scalar_one()
            )
    return counts


def query_dataframe(
    engine: Engine,
    sql: str,
    params: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Run SQL and return a pandas DataFrame."""

    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text(sql), connection, params=params or {})
    except Exception as exc:
        raise QueryExecutionError(f"Failed to execute SQL query: {exc}") from exc


def export_tables_to_csv(engine: Engine, output_dir: Path) -> dict[str, Path]:
    """Export all project tables to CSV files for portfolio review."""

    output_dir.mkdir(parents=True, exist_ok=True)
    exports: dict[str, Path] = {}
    with engine.connect() as connection:
        for table in TABLES_IN_LOAD_ORDER:
            path = output_dir / f"{table.name}.csv"
            dataframe = pd.read_sql_query(text(f"SELECT * FROM {table.name}"), connection)
            dataframe.to_csv(path, index=False)
            exports[table.name] = path
    return exports


def get_database_info(engine: Engine) -> dict[str, Any]:
    """Return database metadata for the dashboard sidebar."""
    info: dict[str, Any] = {}
    try:
        counts = get_table_counts(engine)
        info["table_counts"] = counts
        info["total_rows"] = sum(counts.values())
        info["table_count"] = len(counts)
        
        with engine.connect() as connection:
            # Get last sync time
            result = connection.execute(
                text("SELECT MAX(fetched_at) FROM api_sync_log")
            ).scalar_one_or_none()
            info["last_refresh"] = str(result) if result else "Never"
            
            # Get database file size for SQLite
            if str(engine.url).startswith("sqlite"):
                try:
                    db_size = connection.execute(
                        text("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
                    ).scalar_one()
                    info["size_mb"] = round(db_size / (1024 * 1024), 2)
                except Exception:
                    info["size_mb"] = None
    except Exception as exc:
        logger.warning("Failed to get database info: %s", exc)
    return info


def optimize_database(engine: Engine) -> None:
    """Run SQLite optimizations (VACUUM, ANALYZE)."""
    if not str(engine.url).startswith("sqlite"):
        return
    try:
        with engine.connect() as connection:
            connection.execute(text("PRAGMA optimize"))
            connection.commit()
        logger.info("Database optimization completed")
    except Exception as exc:
        logger.warning("Database optimization failed: %s", exc)
