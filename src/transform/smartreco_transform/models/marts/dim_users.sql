{{ config(materialized='table') }}

WITH users AS (
    SELECT * FROM {{ ref('stg_users') }}
),

user_events AS (
    SELECT
        user_id,
        MIN(event_timestamp) AS first_active_timestamp,
        MAX(event_timestamp) AS last_active_timestamp,
        COUNT(1) AS total_lifetime_interactions
    FROM {{ ref('stg_events') }}
    GROUP BY 1
)

SELECT
    u.user_id,
    u.country,
    u.registration_timestamp,
    COALESCE(e.total_lifetime_interactions, 0) AS total_lifetime_interactions,
    e.first_active_timestamp,
    e.last_active_timestamp
FROM users u
LEFT JOIN user_events e ON u.user_id = e.user_id