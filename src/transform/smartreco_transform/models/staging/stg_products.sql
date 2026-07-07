{{ config(materialized='view') }}

WITH source_data AS (
    SELECT
        product_id::INT AS product_id,
        brand::VARCHAR AS product_brand,
        category::VARCHAR AS category,
        price::NUMERIC(10, 2) AS price,
        rating::NUMERIC(2, 1) AS rating,
        stock::INT AS stock,
        created_at::DATE AS created_at
    FROM raw.products
)

SELECT * FROM source_data