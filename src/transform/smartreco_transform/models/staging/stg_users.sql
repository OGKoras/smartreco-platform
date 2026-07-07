{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        user_id::INT AS user_id,
        age::INT AS age,
        gender::VARCHAR AS gender,
        country::VARCHAR AS country,
        registration_date::TIMESTAMP AS registration_timestamp,
        premium::BOOLEAN AS is_premium
    FROM raw.users
)

SELECT * FROM source_data