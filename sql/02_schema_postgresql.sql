CREATE TABLE IF NOT EXISTS categories (
    category_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS competitions (
    competition_id VARCHAR(50) PRIMARY KEY,
    competition_name VARCHAR(150) NOT NULL,
    parent_id VARCHAR(50),
    type VARCHAR(20) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    level VARCHAR(50),
    category_id VARCHAR(50) NOT NULL REFERENCES categories(category_id),
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_competitions_category_id
    ON competitions(category_id);
CREATE INDEX IF NOT EXISTS idx_competitions_type_gender
    ON competitions(type, gender);
CREATE INDEX IF NOT EXISTS idx_competitions_parent_id
    ON competitions(parent_id);

CREATE TABLE IF NOT EXISTS complexes (
    complex_id VARCHAR(50) PRIMARY KEY,
    complex_name VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id VARCHAR(50) PRIMARY KEY,
    venue_name VARCHAR(120) NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    city_id VARCHAR(50),
    country_name VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    timezone VARCHAR(100) NOT NULL,
    complex_id VARCHAR(50) NOT NULL REFERENCES complexes(complex_id),
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_venues_country_name
    ON venues(country_name);
CREATE INDEX IF NOT EXISTS idx_venues_complex_id
    ON venues(complex_id);

CREATE TABLE IF NOT EXISTS competitors (
    competitor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    country VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    abbreviation VARCHAR(10) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_competitors_country
    ON competitors(country);
CREATE INDEX IF NOT EXISTS idx_competitors_name
    ON competitors(name);

CREATE TABLE IF NOT EXISTS competitor_rankings (
    rank_id SERIAL PRIMARY KEY,
    rank INTEGER NOT NULL,
    movement INTEGER NOT NULL,
    points INTEGER NOT NULL,
    competitions_played INTEGER NOT NULL,
    competitor_id VARCHAR(50) NOT NULL REFERENCES competitors(competitor_id),
    ranking_type_id INTEGER NOT NULL,
    ranking_name VARCHAR(50) NOT NULL,
    ranking_year INTEGER NOT NULL,
    ranking_week INTEGER NOT NULL,
    ranking_gender VARCHAR(10) NOT NULL,
    source_generated_at VARCHAR(40),
    ingested_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rankings_rank_points
    ON competitor_rankings(rank, points);
CREATE INDEX IF NOT EXISTS idx_rankings_competitor_id
    ON competitor_rankings(competitor_id);
CREATE INDEX IF NOT EXISTS idx_rankings_week
    ON competitor_rankings(ranking_year, ranking_week, ranking_name);

CREATE TABLE IF NOT EXISTS api_sync_log (
    sync_id SERIAL PRIMARY KEY,
    endpoint VARCHAR(80) NOT NULL,
    source_generated_at VARCHAR(40),
    fetched_at TIMESTAMPTZ NOT NULL,
    status_code INTEGER NOT NULL,
    row_count INTEGER NOT NULL,
    payload_sha256 VARCHAR(64) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_sync_log_endpoint
    ON api_sync_log(endpoint);

