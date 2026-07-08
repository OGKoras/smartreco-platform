import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from scipy import sparse
from implicit.als import AlternatingLeastSquares
os.environ['OPENBLAS_NUM_THREADS'] = '1'
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

DATABASE_URL = "postgresql://{}:{}@{}:{}/{}".format(USER, PASSWORD, HOST, PORT, DB_NAME)
engine = create_engine(DATABASE_URL)


def load_data():
    print("Loading data...")
    query = """
            SELECT user_id, product_id, COUNT(*) AS interaction_strength
            FROM analytics.fact_events
            WHERE user_id IS NOT NULL \
              AND product_id IS NOT NULL
            GROUP BY user_id, product_id; \
            """
    return pd.read_sql_query(query, engine)


if __name__ == "__main__":
    df = load_data()
    print(f"Success! Loaded {len(df)} interaction rows.")

    user_category = df['user_id'].astype('category')
    product_category = df['product_id'].astype('category')
    df['user_code'] = user_category.cat.codes
    df['product_code'] = product_category.cat.codes

    user_code_to_id = dict(enumerate(user_category.cat.categories))
    product_code_to_id = dict(enumerate(product_category.cat.categories))

    num_unique_users = user_category.nunique()
    num_unique_products = product_category.nunique()

    interaction_matrix = sparse.coo_matrix(
        (
            df['interaction_strength'].astype(float),
            (df['user_code'], df['product_code'])
        ),
        shape=(num_unique_users, num_unique_products)
    ).tocsr()

    print(f"Unique users count:    {interaction_matrix.shape[0]}")
    print(f"Unique products count: {interaction_matrix.shape[1]}")

    model = AlternatingLeastSquares(
        factors=64,
        regularization=0.1,
        iterations=20,
        random_state=42,
    )

    print("Starting ALS model training...")
    model.fit(interaction_matrix)

    target_user_code = 0
    ids, scores = model.recommend(
        userid=target_user_code,
        user_items=interaction_matrix[target_user_code],
        N=10
    )

    real_product_ids = [product_code_to_id[code] for code in ids]
    real_user_id = user_code_to_id[target_user_code]

    print(f"\nRecommendations for DB User ID '{real_user_id}':")
    print("Recommended DB product IDs:", real_product_ids)
    print("Recommendation scores:     ", scores)