{{ config(materialized='table') }}

WITH fact_events AS (
    SELECT * FROM {{ ref('fact_events') }}
),

recent_metrics AS (
    SELECT
        user_id,
        COUNT(CASE WHEN event_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) AS count_interactions_last_7_days,
        COUNT(CASE WHEN event_type = 'click' AND event_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) AS count_clicks_last_7_days,
        COUNT(CASE WHEN event_type = 'purchase' AND event_timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) AS count_purchases_last_7_days,
        MODE() WITHIN GROUP (ORDER BY category) AS favorite_category_last_7_days
    FROM fact_events
    GROUP BY 1
),

session_metrics AS (
    SELECT
        user_id,
        AVG(LEAST(EXTRACT(EPOCH FROM (max_ts - min_ts)) / 60, 120))::NUMERIC(10, 2) AS avg_session_duration_minutes
    FROM (
        SELECT
            user_id,
            DATE(event_timestamp) AS event_date,
            MIN(event_timestamp) AS min_ts,
            MAX(event_timestamp) AS max_ts
        FROM fact_events
        GROUP BY 1, 2
    ) daily_sessions
    GROUP BY 1
)

SELECT
    u.user_id,
    u.country,
    COALESCE(rm.count_interactions_last_7_days, 0) AS count_interactions_last_7_days,
    COALESCE(rm.count_clicks_last_7_days, 0) AS count_clicks_last_7_days,
    COALESCE(rm.count_purchases_last_7_days, 0) AS count_purchases_last_7_days,
    rm.favorite_category_last_7_days,
    COALESCE(sm.avg_daily_session_duration_minutes, 0.00) AS avg_daily_session_duration_minutes
FROM {{ ref('dim_users') }} u
LEFT JOIN recent_metrics rm ON u.user_id = rm.user_id
LEFT JOIN session_metrics sm ON u.user_id = sm.user_id