# Requirements Matrix

| Brief Requirement | Implementation |
| --- | --- |
| Parse and extract data from Sportradar JSON responses using API integration | `tennis_analytics/api_client.py`, `scripts/refresh_data.py` |
| Transform nested JSON structures into a flat relational schema | `tennis_analytics/transformers.py` |
| Create SQL database with well-designed schema, keys, and relationships | `tennis_analytics/database.py`, `sql/01_schema_sqlite.sql`, `sql/02_schema_postgresql.sql`, `sql/03_schema_mysql.sql` |
| Collect competition data | Populated `categories` and `competitions` tables |
| Collect complexes data | Populated `complexes` and `venues` tables |
| Collect doubles competitor rankings data | Populated `competitors` and `competitor_rankings` tables |
| Execute required SQL queries | `sql/04_analysis_queries.sql`, `tennis_analytics/queries.py`, Streamlit SQL Analysis page |
| Build Streamlit app connected to SQL database | `app.py` |
| Dashboard summary statistics | Overview page metrics for competitions, venues, competitors, countries, categories, complexes, max points, and stable rankings |
| Search/filter competitors | Competitors page search, country, ranking, rank range, points, and movement filters |
| Competitor details viewer | Competitors page selected-player detail metrics |
| Country-wise analysis | Overview and Competitors pages, plus SQL query catalog |
| Leaderboards | Competitors page top rank and points tables |
| Error handling for API/database/user inputs | Retry logic, rate-limit wait, explicit missing-key error, Streamlit sidebar error display |
| Documentation | `README.md`, `docs/report.md`, `docs/schema_design.md`, `docs/sql_queries.md`, this matrix |
| Testing and project completeness | Unit tests, compile validation, live database refresh, SQL execution verification |

