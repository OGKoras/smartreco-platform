from fastapi import FastAPI
import os
import redis
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable '{key}'. "
            f"Please verify that the .env file exists and contains this variable."
        )
    return value

USER = require_env("POSTGRES_USER")
PASSWORD = require_env("POSTGRES_PASSWORD")
DB_NAME = require_env("POSTGRES_DB")
HOST = os.getenv("POSTGRES_HOST", "localhost")
PORT = os.getenv("POSTGRES_PORT", "5432")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

DATABASE_URL = "postgresql://{}:{}@{}:{}/{}".format(USER, PASSWORD, HOST, PORT, DB_NAME)

MAX_RETRIES = 10
RETRY_DELAY_SECONDS = 3
app = FastAPI()
engine = create_engine(DATABASE_URL)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
@app.get("/users/{user_id}/recommendations")
def get_recommendations(user_id: int):
    cache_key = f"user:reco:{user_id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    query = text("""
        WITH last_category AS (
            SELECT p.category
            FROM raw.events e
            JOIN raw.products p ON e.product_id = p.product_id
            WHERE e.user_id = :user_id
            ORDER BY e.timestamp DESC
            LIMIT 1
        )
        SELECT product_id, rating AS score
        FROM raw.products
        WHERE category = (SELECT category FROM last_category)
           OR (SELECT category FROM last_category) IS NULL
        ORDER BY RANDOM()
        LIMIT 5;
    """)

    recommendations = []
    with engine.connect() as conn:
        result = conn.execute(query, {"user_id": user_id})
        for row in result:
            recommendations.append({
                "product_id": row[0],
                "score": float(row[1]),
            })

    redis_client.setex(cache_key, 60, json.dumps(recommendations))

    return recommendations
