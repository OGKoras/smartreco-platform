from fastapi import FastAPI
import os
import redis
from dotenv import load_dotenv
from sqlalchemy import create_engine
from scipy import sparse
import mlflow
import mlflow.sklearn
from contextlib import asynccontextmanager
from mlflow.tracking import MlflowClient
import json

RECOMMENDER_MODEL = None
USER_MAPPING = {}
PRODUCT_MAPPING = {}
TRAIN_INTERACTION_MATRIX = None
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

mlflow.set_tracking_uri("http://localhost:5000")
engine = create_engine(DATABASE_URL)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global RECOMMENDER_MODEL, USER_MAPPING, PRODUCT_MAPPING, TRAIN_INTERACTION_MATRIX

    print("Searching for the latest model in MLflow...")
    client = MlflowClient()

    experiment = client.get_experiment_by_name("smartreco-als")
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string="status = 'FINISHED'",
        order_by=["attributes.start_time DESC"],
        max_results=1
    )

    if not runs:
        raise RuntimeError("No successful runs in MLflow for this experiment!")

    latest_run_id = runs[0].info.run_id
    print(f"Found the latest Run ID: {latest_run_id}")

    model_uri = f"runs:/{latest_run_id}/model"
    RECOMMENDER_MODEL = mlflow.sklearn.load_model(model_uri)

    local_user_path = client.download_artifacts(latest_run_id, "mappings/user_id_to_code.json")
    local_product_path = client.download_artifacts(latest_run_id, "mappings/product_code_to_id.json")
    local_matrix_path = client.download_artifacts(latest_run_id, "matrices/interaction_matrix.npz")

    with open(local_user_path, "r") as f:
        USER_MAPPING = json.load(f)
    with open(local_product_path, "r") as f:
        PRODUCT_MAPPING = json.load(f)

    TRAIN_INTERACTION_MATRIX = sparse.load_npz(local_matrix_path)

    print("All model components and mappings loaded successfully!")

    yield

    print("Shutting down the application...")

app = FastAPI(lifespan=lifespan)
@app.get("/users/{user_id}/recommendations")
def get_recommendations(user_id: int):
    cache_key = f"user:reco:{user_id}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    str_user_id = str(user_id)
    recommendations = []
    if str_user_id not in USER_MAPPING:
        print(f"User {user_id} not found in the model. Returning fallback (most popular)...")
        return [{"product_id": 9999, "score": 0.0, "note": "Cold-start fallback"}]
    user_code = USER_MAPPING[str_user_id]
    user_profile_interactions = TRAIN_INTERACTION_MATRIX[user_code]

    ids, scores = RECOMMENDER_MODEL.recommend(
        userid=user_code,
        user_items=user_profile_interactions,
        N=10
    )
    for product_code, score in zip(ids.tolist(), scores.tolist()):
        str_product_code = str(product_code)
        if str_product_code in PRODUCT_MAPPING:
            real_product_id = PRODUCT_MAPPING[str_product_code]
            recommendations.append({
                "product_id": real_product_id,
                "score": float(score)
            })


    redis_client.setex(cache_key, 60, json.dumps(recommendations))

    return recommendations
