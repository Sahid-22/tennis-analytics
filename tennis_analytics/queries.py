"""SQL query catalog used by the app and documentation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuerySpec:
    title: str
    sql: str
    params: tuple[str, ...] = ()
    default_params: dict[str, object] | None = None


REQUIRED_QUERIES: dict[str, list[QuerySpec]] = {
    "Competition Analysis": [
        QuerySpec(
            "List all competitions along with their category name",
            """
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
            """,
        ),
        QuerySpec(
            "Count the number of competitions in each category",
            """
            SELECT
                cat.category_name,
                COUNT(*) AS competition_count
            FROM competitions AS c
            INNER JOIN categories AS cat
                ON c.category_id = cat.category_id
            GROUP BY cat.category_name
            ORDER BY competition_count DESC, cat.category_name;
            """,
        ),
        QuerySpec(
            "Find all competitions of type 'doubles'",
            """
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
            """,
        ),
        QuerySpec(
            "Get competitions that belong to a specific category",
            """
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
            """,
            params=("category_name",),
            default_params={"category_name": "ITF Men"},
        ),
        QuerySpec(
            "Identify parent competitions and their sub-competitions",
            """
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
            """,
        ),
        QuerySpec(
            "Analyze the distribution of competition types by category",
            """
            SELECT
                cat.category_name,
                c.type,
                COUNT(*) AS competition_count
            FROM competitions AS c
            INNER JOIN categories AS cat
                ON c.category_id = cat.category_id
            GROUP BY cat.category_name, c.type
            ORDER BY cat.category_name, competition_count DESC;
            """,
        ),
        QuerySpec(
            "List all competitions with no parent",
            """
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
            """,
        ),
    ],
    "Complex and Venue Analysis": [
        QuerySpec(
            "List all venues along with their associated complex name",
            """
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
            """,
        ),
        QuerySpec(
            "Count the number of venues in each complex",
            """
            SELECT
                cx.complex_name,
                COUNT(v.venue_id) AS venue_count
            FROM complexes AS cx
            LEFT JOIN venues AS v
                ON v.complex_id = cx.complex_id
            GROUP BY cx.complex_id, cx.complex_name
            ORDER BY venue_count DESC, cx.complex_name;
            """,
        ),
        QuerySpec(
            "Get details of venues in a specific country",
            """
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
            """,
            params=("country_name",),
            default_params={"country_name": "Chile"},
        ),
        QuerySpec(
            "Identify all venues and their timezones",
            """
            SELECT
                venue_name,
                city_name,
                country_name,
                timezone
            FROM venues
            ORDER BY country_name, city_name, venue_name;
            """,
        ),
        QuerySpec(
            "Find complexes that have more than one venue",
            """
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
            """,
        ),
        QuerySpec(
            "List venues grouped by country",
            """
            SELECT
                country_name,
                COUNT(*) AS venue_count,
                COUNT(DISTINCT city_name) AS city_count
            FROM venues
            GROUP BY country_name
            ORDER BY venue_count DESC, country_name;
            """,
        ),
        QuerySpec(
            "Find all venues for a specific complex",
            """
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
            """,
            params=("complex_name",),
            default_params={"complex_name": "Nacional"},
        ),
    ],
    "Doubles Ranking Analysis": [
        QuerySpec(
            "Get all competitors with their rank and points",
            """
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
            """,
        ),
        QuerySpec(
            "Find competitors ranked in the top 5",
            """
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
            """,
        ),
        QuerySpec(
            "List competitors with no rank movement",
            """
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
            """,
        ),
        QuerySpec(
            "Get the total points of competitors from a specific country",
            """
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
            """,
            params=("country_name",),
            default_params={"country_name": "Croatia"},
        ),
        QuerySpec(
            "Count the number of competitors per country",
            """
            SELECT
                cmp.country,
                COUNT(*) AS competitor_count
            FROM competitor_rankings AS cr
            INNER JOIN competitors AS cmp
                ON cr.competitor_id = cmp.competitor_id
            GROUP BY cmp.country
            ORDER BY competitor_count DESC, cmp.country;
            """,
        ),
        QuerySpec(
            "Find competitors with the highest points in the current week",
            """
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
            """,
        ),
    ],
}


EXTRA_INSIGHT_QUERIES: dict[str, QuerySpec] = {
    "Country ranking power index": QuerySpec(
        "Country ranking power index",
        """
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
        """,
    ),
    "Competition portfolio by level": QuerySpec(
        "Competition portfolio by level",
        """
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
        """,
    ),
    "Venue timezone spread": QuerySpec(
        "Venue timezone spread",
        """
        SELECT
            timezone,
            COUNT(*) AS venue_count,
            COUNT(DISTINCT country_name) AS country_count
        FROM venues
        GROUP BY timezone
        ORDER BY venue_count DESC, timezone;
        """,
    ),
}

ADVANCED_QUERIES: dict[str, QuerySpec] = {
    "Country Dominance Matrix": QuerySpec(
        "Country Dominance Matrix",
        """
        SELECT
            cmp.country,
            cr.ranking_name,
            COUNT(*) AS competitor_count,
            SUM(cr.points) AS total_points,
            ROUND(AVG(cr.rank), 1) AS avg_rank,
            MIN(cr.rank) AS best_rank,
            MAX(cr.points) AS max_points
        FROM competitor_rankings AS cr
        INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
        GROUP BY cmp.country, cr.ranking_name
        ORDER BY total_points DESC;
        """,
    ),
    "Competition Type Gender Cross-Tab": QuerySpec(
        "Competition Type Gender Cross-Tab",
        """
        SELECT
            type,
            gender,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM competitions), 1) AS percentage
        FROM competitions
        GROUP BY type, gender
        ORDER BY count DESC;
        """,
    ),
    "Ranking Movement Leaders": QuerySpec(
        "Ranking Movement Leaders",
        """
        SELECT
            cmp.name,
            cmp.country,
            cr.ranking_name,
            cr.rank,
            cr.points,
            cr.movement,
            cr.competitions_played,
            CASE
                WHEN cr.movement > 0 THEN 'Climber'
                WHEN cr.movement < 0 THEN 'Faller'
                ELSE 'Stable'
            END AS movement_category
        FROM competitor_rankings AS cr
        INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
        WHERE cr.movement <> 0
        ORDER BY ABS(cr.movement) DESC, cr.points DESC
        LIMIT 50;
        """,
    ),
    "Points Distribution by Country": QuerySpec(
        "Points Distribution by Country",
        """
        SELECT
            cmp.country,
            MIN(cr.points) AS min_points,
            MAX(cr.points) AS max_points,
            ROUND(AVG(cr.points), 1) AS avg_points,
            SUM(cr.points) AS total_points,
            COUNT(*) AS competitor_count
        FROM competitor_rankings AS cr
        INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
        GROUP BY cmp.country
        HAVING COUNT(*) >= 3
        ORDER BY avg_points DESC;
        """,
    ),
    "Competitions Played vs Rank Correlation": QuerySpec(
        "Competitions Played vs Rank Correlation",
        """
        SELECT
            cr.rank,
            cr.points,
            cr.competitions_played,
            cr.movement,
            cmp.name,
            cmp.country,
            cr.ranking_name
        FROM competitor_rankings AS cr
        INNER JOIN competitors AS cmp ON cr.competitor_id = cmp.competitor_id
        ORDER BY cr.rank;
        """,
    ),
    "Venue Geographic Coverage": QuerySpec(
        "Venue Geographic Coverage",
        """
        SELECT
            v.country_name,
            v.country_code,
            COUNT(DISTINCT v.venue_id) AS venue_count,
            COUNT(DISTINCT v.city_name) AS city_count,
            COUNT(DISTINCT cx.complex_id) AS complex_count,
            COUNT(DISTINCT v.timezone) AS timezone_count
        FROM venues AS v
        INNER JOIN complexes AS cx ON v.complex_id = cx.complex_id
        GROUP BY v.country_name, v.country_code
        ORDER BY venue_count DESC;
        """,
    ),
    "Category Depth Analysis": QuerySpec(
        "Category Depth Analysis",
        """
        SELECT
            cat.category_name,
            COUNT(c.competition_id) AS total_competitions,
            COUNT(CASE WHEN c.parent_id IS NULL THEN 1 END) AS root_competitions,
            COUNT(CASE WHEN c.parent_id IS NOT NULL THEN 1 END) AS sub_competitions,
            COUNT(DISTINCT c.type) AS type_variety,
            COUNT(DISTINCT c.gender) AS gender_variety
        FROM categories AS cat
        INNER JOIN competitions AS c ON c.category_id = cat.category_id
        GROUP BY cat.category_name
        ORDER BY total_competitions DESC;
        """,
    ),
}

