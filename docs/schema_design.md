# Schema Design

The schema follows a normalized dimensional pattern. API entities are stored once and analysis tables reference them through stable Sportradar IDs.

## Tables

| Table | Purpose | Primary Key | Key Relationships |
| --- | --- | --- | --- |
| categories | Competition category dimension such as ATP, WTA, ITF Men, ITF Women | `category_id` | Referenced by `competitions.category_id` |
| competitions | Competition/event catalog with type, gender, level, parent hierarchy, and category | `competition_id` | References `categories.category_id`; `parent_id` stores hierarchy |
| complexes | Sports complex dimension | `complex_id` | Referenced by `venues.complex_id` |
| venues | Venue dimension with city, country, timezone, and complex linkage | `venue_id` | References `complexes.complex_id` |
| competitors | Doubles competitor dimension | `competitor_id` | Referenced by `competitor_rankings.competitor_id` |
| competitor_rankings | Weekly doubles ranking fact table with rank, movement, points, competitions played, league, year, and week | `rank_id` | References `competitors.competitor_id` |
| api_sync_log | Refresh audit table for source freshness, HTTP status, row counts, and payload checksum | `sync_id` | Standalone audit table |

## Normalization Choices

- Categories are separated from competitions to prevent repeated category names and enable category-level analysis.
- Complexes are separated from venues because one complex can contain many venues.
- Competitors are separated from rankings because ranking facts can evolve by week while competitor identity is stable.
- Ranking metadata (`ranking_name`, `ranking_year`, `ranking_week`, `ranking_gender`) is stored on `competitor_rankings` so ATP/WTA snapshots can be analyzed independently.
- The `api_sync_log` table supports traceability for dashboard freshness and data-quality review.

## Indexing Strategy

- `competitions.category_id`, `competitions.type`, `competitions.gender`, and `competitions.parent_id` accelerate filters and hierarchy queries.
- `venues.country_name` and `venues.complex_id` accelerate country and complex exploration.
- `competitors.country` and `competitors.name` support search and country analysis.
- `competitor_rankings.rank`, `competitor_rankings.points`, `competitor_rankings.competitor_id`, and ranking week indexes support leaderboard and latest-week queries.

## Database Compatibility

The application uses SQLAlchemy and defaults to SQLite for local review. Equivalent PostgreSQL and MySQL schema files are included in `sql/` for production-style deployment.

