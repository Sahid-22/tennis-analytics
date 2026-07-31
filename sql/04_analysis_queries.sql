-- Competition analysis

-- 1. List all competitions along with their category name.
SELECT
    c.competition_id,
    c.competition_name,
    c.type,
    c.gender,
    COALESCE(c.level, 'Unspecified') AS level,
    cat.category_name
FROM competitions AS c
INNER JOIN categories AS cat
    ON c.category_id = cat.category_id
ORDER BY cat.category_name, c.competition_name;

-- 2. Count the number of competitions in each category.
SELECT
    cat.category_name,
    COUNT(*) AS competition_count
FROM competitions AS c
INNER JOIN categories AS cat
    ON c.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY competition_count DESC, cat.category_name;

-- 3. Find all competitions of type 'doubles'.
SELECT
    c.competition_id,
    c.competition_name,
    cat.category_name,
    c.gender,
    COALESCE(c.level, 'Unspecified') AS level
FROM competitions AS c
INNER JOIN categories AS cat
    ON c.category_id = cat.category_id
WHERE LOWER(c.type) = 'doubles'
ORDER BY cat.category_name, c.competition_name;

-- 4. Get competitions that belong to a specific category.
-- Bind :category_name, for example 'ITF Men'.
SELECT
    c.competition_id,
    c.competition_name,
    c.type,
    c.gender,
    COALESCE(c.level, 'Unspecified') AS level
FROM competitions AS c
INNER JOIN categories AS cat
    ON c.category_id = cat.category_id
WHERE cat.category_name = :category_name
ORDER BY c.competition_name;

-- 5. Identify parent competitions and their sub-competitions.
SELECT
    parent.competition_id AS parent_competition_id,
    parent.competition_name AS parent_competition_name,
    child.competition_id AS child_competition_id,
    child.competition_name AS child_competition_name,
    child.type AS child_type,
    child.gender AS child_gender
FROM competitions AS parent
INNER JOIN competitions AS child
    ON child.parent_id = parent.competition_id
ORDER BY parent.competition_name, child.competition_name;

-- 6. Analyze the distribution of competition types by category.
SELECT
    cat.category_name,
    c.type,
    COUNT(*) AS competition_count
FROM competitions AS c
INNER JOIN categories AS cat
    ON c.category_id = cat.category_id
GROUP BY cat.category_name, c.type
ORDER BY cat.category_name, competition_count DESC;

-- 7. List all competitions with no parent.
SELECT
    c.competition_id,
    c.competition_name,
    c.type,
    c.gender,
    cat.category_name
FROM competitions AS c
INNER JOIN categories AS cat
    ON c.category_id = cat.category_id
WHERE c.parent_id IS NULL
ORDER BY cat.category_name, c.competition_name;

-- Complex and venue analysis

-- 1. List all venues along with their associated complex name.
SELECT
    v.venue_id,
    v.venue_name,
    v.city_name,
    v.country_name,
    v.timezone,
    cx.complex_name
FROM venues AS v
INNER JOIN complexes AS cx
    ON v.complex_id = cx.complex_id
ORDER BY cx.complex_name, v.venue_name;

-- 2. Count the number of venues in each complex.
SELECT
    cx.complex_name,
    COUNT(v.venue_id) AS venue_count
FROM complexes AS cx
LEFT JOIN venues AS v
    ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
ORDER BY venue_count DESC, cx.complex_name;

-- 3. Get details of venues in a specific country.
-- Bind :country_name, for example 'Chile'.
SELECT
    v.venue_id,
    v.venue_name,
    v.city_name,
    v.country_name,
    v.country_code,
    v.timezone,
    cx.complex_name
FROM venues AS v
INNER JOIN complexes AS cx
    ON v.complex_id = cx.complex_id
WHERE v.country_name = :country_name
ORDER BY v.city_name, cx.complex_name, v.venue_name;

-- 4. Identify all venues and their timezones.
SELECT
    venue_name,
    city_name,
    country_name,
    timezone
FROM venues
ORDER BY country_name, city_name, venue_name;

-- 5. Find complexes that have more than one venue.
SELECT
    cx.complex_id,
    cx.complex_name,
    COUNT(v.venue_id) AS venue_count
FROM complexes AS cx
INNER JOIN venues AS v
    ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name
HAVING COUNT(v.venue_id) > 1
ORDER BY venue_count DESC, cx.complex_name;

-- 6. List venues grouped by country.
SELECT
    country_name,
    COUNT(*) AS venue_count,
    COUNT(DISTINCT city_name) AS city_count
FROM venues
GROUP BY country_name
ORDER BY venue_count DESC, country_name;

-- 7. Find all venues for a specific complex.
-- Bind :complex_name, for example 'Nacional'.
SELECT
    v.venue_id,
    v.venue_name,
    v.city_name,
    v.country_name,
    v.timezone
FROM venues AS v
INNER JOIN complexes AS cx
    ON v.complex_id = cx.complex_id
WHERE cx.complex_name = :complex_name
ORDER BY v.venue_name;

-- Doubles competitor ranking analysis

-- 1. Get all competitors with their rank and points.
SELECT
    cmp.competitor_id,
    cmp.name,
    cmp.country,
    cr.ranking_name,
    cr.ranking_gender,
    cr.rank,
    cr.points,
    cr.movement,
    cr.competitions_played
FROM competitor_rankings AS cr
INNER JOIN competitors AS cmp
    ON cr.competitor_id = cmp.competitor_id
ORDER BY cr.ranking_name, cr.rank, cmp.name;

-- 2. Find competitors ranked in the top 5.
SELECT
    cmp.name,
    cmp.country,
    cr.ranking_name,
    cr.rank,
    cr.points,
    cr.movement
FROM competitor_rankings AS cr
INNER JOIN competitors AS cmp
    ON cr.competitor_id = cmp.competitor_id
WHERE cr.rank <= 5
ORDER BY cr.ranking_name, cr.rank, cr.points DESC;

-- 3. List competitors with no rank movement.
SELECT
    cmp.name,
    cmp.country,
    cr.ranking_name,
    cr.rank,
    cr.points,
    cr.competitions_played
FROM competitor_rankings AS cr
INNER JOIN competitors AS cmp
    ON cr.competitor_id = cmp.competitor_id
WHERE cr.movement = 0
ORDER BY cr.ranking_name, cr.rank, cmp.name;

-- 4. Get the total points of competitors from a specific country.
-- Bind :country_name, for example 'Croatia'.
SELECT
    cmp.country,
    COUNT(*) AS competitor_count,
    SUM(cr.points) AS total_points,
    ROUND(AVG(cr.points), 2) AS average_points
FROM competitor_rankings AS cr
INNER JOIN competitors AS cmp
    ON cr.competitor_id = cmp.competitor_id
WHERE cmp.country = :country_name
GROUP BY cmp.country;

-- 5. Count the number of competitors per country.
SELECT
    cmp.country,
    COUNT(*) AS competitor_count
FROM competitor_rankings AS cr
INNER JOIN competitors AS cmp
    ON cr.competitor_id = cmp.competitor_id
GROUP BY cmp.country
ORDER BY competitor_count DESC, cmp.country;

-- 6. Find competitors with the highest points in the current week.
WITH latest_week AS (
    SELECT ranking_year, ranking_week
    FROM competitor_rankings
    ORDER BY ranking_year DESC, ranking_week DESC
    LIMIT 1
),
latest_rankings AS (
    SELECT cr.*
    FROM competitor_rankings AS cr
    INNER JOIN latest_week AS lw
        ON cr.ranking_year = lw.ranking_year
        AND cr.ranking_week = lw.ranking_week
),
max_points AS (
    SELECT MAX(points) AS highest_points
    FROM latest_rankings
)
SELECT
    cmp.name,
    cmp.country,
    lr.ranking_name,
    lr.ranking_year,
    lr.ranking_week,
    lr.rank,
    lr.points
FROM latest_rankings AS lr
INNER JOIN competitors AS cmp
    ON lr.competitor_id = cmp.competitor_id
INNER JOIN max_points AS mp
    ON lr.points = mp.highest_points
ORDER BY lr.ranking_name, cmp.name;

-- Additional insight query: country ranking power index.
SELECT
    cmp.country,
    COUNT(*) AS competitor_count,
    ROUND(AVG(cr.points), 2) AS average_points,
    SUM(cr.points) AS total_points,
    MIN(cr.rank) AS best_rank,
    ROUND(SUM(cr.points) * 1.0 / NULLIF(MIN(cr.rank), 0), 2) AS power_index
FROM competitor_rankings AS cr
INNER JOIN competitors AS cmp
    ON cr.competitor_id = cmp.competitor_id
GROUP BY cmp.country
HAVING COUNT(*) >= 2
ORDER BY power_index DESC, total_points DESC;

-- Additional insight query: competition portfolio by level.
SELECT
    cat.category_name,
    COALESCE(c.level, 'Unspecified') AS level,
    c.gender,
    COUNT(*) AS competition_count
FROM competitions AS c
INNER JOIN categories AS cat
    ON c.category_id = cat.category_id
GROUP BY cat.category_name, COALESCE(c.level, 'Unspecified'), c.gender
ORDER BY competition_count DESC, cat.category_name;

-- Additional insight query: venue timezone spread.
SELECT
    timezone,
    COUNT(*) AS venue_count,
    COUNT(DISTINCT country_name) AS country_count
FROM venues
GROUP BY timezone
ORDER BY venue_count DESC, timezone;

