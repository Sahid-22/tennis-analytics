# SQL Query Guide

The executable SQL deliverable is `sql/04_analysis_queries.sql`. It contains every query requested in the brief plus three additional insight queries.

## Competition Analysis Queries

1. List all competitions along with their category name.
2. Count the number of competitions in each category.
3. Find all competitions of type `doubles`.
4. Get competitions that belong to a specific category, default example `ITF Men`.
5. Identify parent competitions and their sub-competitions.
6. Analyze the distribution of competition types by category.
7. List all competitions with no parent.

## Complex and Venue Analysis Queries

1. List all venues along with their associated complex name.
2. Count the number of venues in each complex.
3. Get details of venues in a specific country, default example `Chile`.
4. Identify all venues and their timezones.
5. Find complexes that have more than one venue.
6. List venues grouped by country.
7. Find all venues for a specific complex, default example `Nacional`.

## Doubles Competitor Ranking Queries

1. Get all competitors with their rank and points.
2. Find competitors ranked in the top 5.
3. List competitors with no rank movement.
4. Get the total points of competitors from a specific country, default example `Croatia`.
5. Count the number of competitors per country.
6. Find competitors with the highest points in the current week.

## Additional Insight Queries

1. Country ranking power index.
2. Competition portfolio by level.
3. Venue timezone spread.

All of these queries are also available inside the Streamlit `SQL Analysis` page through `tennis_analytics/queries.py`, which keeps the dashboard and SQL deliverable in sync.

