{{ config(materialized='table') }}

WITH events AS (
    SELECT * FROM {{ ref('stg_events') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
)

SELECT
    e.event_id AS event_key,
    e.user_id,
    e.product_id,
    p.product_brand,
    p.category,
    e.event_type,
    e.event_timestamp
FROM events e
LEFT JOIN products p ON e.product_id = p.product_id