# Project Report

## Objective

Build a complete sports analytics workflow for tennis data from the Sportradar API: extract data, transform nested JSON into relational tables, run SQL analysis, and deliver an interactive Streamlit application.

## Workflow

1. Fetch live JSON payloads from the Sportradar Tennis v3 endpoints for competitions, complexes, and doubles competitor rankings.
2. Persist raw payloads as timestamped JSON snapshots for reproducibility.
3. Normalize nested JSON into categories, competitions, complexes, venues, competitors, and ranking fact tables.
4. Rebuild the SQL database in one transaction to keep the app reading a consistent snapshot.
5. Export table-level CSVs for review and downstream analysis.
6. Serve Streamlit dashboards and query results from the SQL database.

## Live Data Snapshot

The database was refreshed on 2026-07-21. Source payload timestamps from Sportradar were:

| Endpoint | Source generated at | Rows loaded |
| --- | --- | ---: |
| competitions | 2026-07-21T14:23:52+00:00 | 6,619 |
| complexes | 2026-07-21T14:22:57+00:00 | 767 |
| doubles_rankings | 2026-07-21T14:20:59+00:00 | 1,000 |

## Key Insights

- ITF Men has the largest competition catalog with 2,198 competitions, followed by ITF Women with 2,032 and Challenger with 1,043.
- Singles competitions lead the portfolio with 3,562 records, while doubles has 3,039.
- The USA has the largest doubles ranking representation in the current snapshot with 110 competitors and 85,307 total points.
- Katerina Siniakova leads the loaded doubles rankings by points with 10,150 WTA points.
- Venue coverage is broadest in the USA with 653 venues, followed by Italy, France, China, and Spain.

## Dashboard Design

The Streamlit app is organized around the main user workflows:

- Overview for executive metrics, category charts, country ranking coverage, and API freshness.
- Competitions for category, type, gender, level filters, pagination, distributions, and hierarchy exploration.
- Competitors for search, rank range, country, league, points, movement filters, detail view, and leaderboards.
- Venues for country/complex exploration, venue footprint charts, and multi-venue complex discovery.
- SQL Analysis for running every required query and additional insight queries directly from the app.

## Reliability and Error Handling

- API requests use explicit timeouts.
- HTTP 429 and 5xx responses are retried with backoff and `Retry-After` support.
- Missing API keys raise actionable errors.
- Database writes are transactional.
- Raw JSON snapshots and payload checksums support auditability.
- Streamlit displays friendly errors for refresh failures.

## Challenges and Decisions

- The brief lists MySQL/PostgreSQL, but a local SQLite database is included so the project is runnable without requiring a server. PostgreSQL and MySQL schema files are supplied for migration.
- Sportradar ranking payloads include ATP and WTA ranking groups, so ranking metadata is retained in the fact table for richer filtering.
- Some API fields can be missing; the transform layer normalizes missing country codes to `UNK` and optional strings to safe defaults.
- The app uses pagination for larger tables and SQL filters for common exploration paths.

## Validation Summary

- `python -m compileall tennis_analytics scripts app.py tests` passed.
- `python -m unittest discover -s tests -v` passed with 3 tests.
- All required SQL queries executed successfully against the populated database.
- Streamlit returned HTTP 200 at `http://127.0.0.1:8501`.

