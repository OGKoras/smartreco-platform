{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        event_id::BIGINT AS event_id,
        user_id::INT AS user_id,
        product_id::INT AS product_id,
        event_type::VARCHAR AS event_type,
        timestamp::TIMESTAMP AS event_timestamp,
        session_id::VARCHAR AS session_id,
        device::VARCHAR AS device
    FROM raw.events
)

SELECT * FROM source_data