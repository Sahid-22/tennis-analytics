CREATE TABLE IF NOT EXISTS categories (
    category_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    ingested_at DATETIME NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS competitions (
    competition_id VARCHAR(50) PRIMARY KEY,
    competition_name VARCHAR(150) NOT NULL,
    parent_id VARCHAR(50),
    type VARCHAR(20) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    level VARCHAR(50),
    category_id VARCHAR(50) NOT NULL,
    ingested_at DATETIME NOT NULL,
    CONSTRAINT fk_competitions_categories
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
) ENGINE=InnoDB;

CREATE INDEX idx_competitions_category_id
    ON competitions(category_id);
CREATE INDEX idx_competitions_type_gender
    ON competitions(type, gender);
CREATE INDEX idx_competitions_parent_id
    ON competitions(parent_id);

CREATE TABLE IF NOT EXISTS complexes (
    complex_id VARCHAR(50) PRIMARY KEY,
    complex_name VARCHAR(100) NOT NULL,
    ingested_at DATETIME NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS venues (
    venue_id VARCHAR(50) PRIMARY KEY,
    venue_name VARCHAR(120) NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    city_id VARCHAR(50),
    country_name VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    timezone VARCHAR(100) NOT NULL,
    complex_id VARCHAR(50) NOT NULL,
    ingested_at DATETIME NOT NULL,
    CONSTRAINT fk_venues_complexes
        FOREIGN KEY (complex_id) REFERENCES complexes(complex_id)
) ENGINE=InnoDB;

CREATE INDEX idx_venues_country_name
    ON venues(country_name);
CREATE INDEX idx_venues_complex_id
    ON venues(complex_id);

CREATE TABLE IF NOT EXISTS competitors (
    competitor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    country VARCHAR(100) NOT NULL,
    country_code CHAR(3) NOT NULL,
    abbreviation VARCHAR(10) NOT NULL,
    ingested_at DATETIME NOT NULL
) ENGINE=InnoDB;

CREATE INDEX idx_competitors_country
    ON competitors(country);
CREATE INDEX idx_competitors_name
    ON competitors(name);

CREATE TABLE IF NOT EXISTS competitor_rankings (
    rank_id INT AUTO_INCREMENT PRIMARY KEY,
    rank INT NOT NULL,
    movement INT NOT NULL,
    points INT NOT NULL,
    competitions_played INT NOT NULL,
    competitor_id VARCHAR(50) NOT NULL,
    ranking_type_id INT NOT NULL,
    ranking_name VARCHAR(50) NOT NULL,
    ranking_year INT NOT NULL,
    ranking_week INT NOT NULL,
    ranking_gender VARCHAR(10) NOT NULL,
    source_generated_at VARCHAR(40),
    ingested_at DATETIME NOT NULL,
    CONSTRAINT fk_rankings_competitors
        FOREIGN KEY (competitor_id) REFERENCES competitors(competitor_id)
) ENGINE=InnoDB;

CREATE INDEX idx_rankings_rank_points
    ON competitor_rankings(rank, points);
CREATE INDEX idx_rankings_competitor_id
    ON competitor_rankings(competitor_id);
CREATE INDEX idx_rankings_week
    ON competitor_rankings(ranking_year, ranking_week, ranking_name);

CREATE TABLE IF NOT EXISTS api_sync_log (
    sync_id INT AUTO_INCREMENT PRIMARY KEY,
    endpoint VARCHAR(80) NOT NULL,
    source_generated_at VARCHAR(40),
    fetched_at DATETIME NOT NULL,
    status_code INT NOT NULL,
    row_count INT NOT NULL,
    payload_sha256 VARCHAR(64) NOT NULL
) ENGINE=InnoDB;

CREATE INDEX idx_api_sync_log_endpoint
    ON api_sync_log(endpoint);

