import os
import sys
import time

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

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

MAX_RETRIES = 10
RETRY_DELAY_SECONDS = 3

DATA_FILES = {
    "users_data.csv": "users",
    "products_data.csv": "products",
    "events_data.csv": "events",
    "orders_data.csv": "orders",
    "marketing_data.csv": "marketing",
}


def wait_for_postgres(engine):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Connection to PostgreSQL established (próba {}/{}).".format(attempt, MAX_RETRIES))
            return
        except OperationalError as e:
            print(
                "Database not ready yet (attempt {}/{}): {}".format(
                    attempt, MAX_RETRIES, str(e).splitlines()[0]
                )
            )
            time.sleep(RETRY_DELAY_SECONDS)
    print("Failed to connect to PostgreSQL after {} attempts. Aborting.".format(MAX_RETRIES))
    sys.exit(1)


def main():
    engine = create_engine(DATABASE_URL)

    wait_for_postgres(engine)

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()
        print("Schema 'raw' has been prepared.")

    for file_name, table_name in DATA_FILES.items():
        if not os.path.exists(file_name):
            print("Skipped '{}' — file does not exist in the current directory.".format(file_name))
            continue

        print("Loading data from '{}'".format(file_name))
        df = pd.read_csv(file_name)
        df.to_sql(name=table_name, con=engine, schema="raw", if_exists="replace", index=False)
        print("Loaded {} rows into raw.{}".format(len(df), table_name))

    print("Loading data ended successfully")


if __name__ == "__main__":
    main()