import os
import random
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

BATCH_SIZE = int(os.getenv("FRESH_EVENTS_BATCH_SIZE", "1000"))

EVENT_TYPES = [
    "view", "click", "add_to_cart",
    "purchase", "remove_from_cart", "wishlist"
]
EVENT_WEIGHTS = [45, 25, 12, 6, 4, 8]
DEVICES = ["mobile", "desktop", "laptop"]


def create_database_url():
    required = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
    )


def main():
    if BATCH_SIZE <= 0:
        raise ValueError("FRESH_EVENTS_BATCH_SIZE must be greater than zero")

    # Airflow supplies the same DAG run ID when retrying a task.
    # A UUID is used only when running the script outside Airflow.
    batch_key = (
        os.getenv("FRESH_EVENTS_BATCH_KEY")
        or os.getenv("AIRFLOW_CTX_DAG_RUN_ID")
        or f"local-{uuid.uuid4()}"
    )

    engine = create_engine(create_database_url())

    try:
        with engine.begin() as conn:
            # Create a small audit table to track processed batches.
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS raw.ingestion_batches (
                    batch_key TEXT PRIMARY KEY,
                    first_event_id BIGINT NOT NULL,
                    last_event_id BIGINT NOT NULL,
                    event_count INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))


            conn.execute(
                text("SELECT pg_advisory_xact_lock(8745201)")
            )

            existing_batch = conn.execute(
                text("""
                    SELECT event_count, first_event_id, last_event_id
                    FROM raw.ingestion_batches
                    WHERE batch_key = :batch_key
                """),
                {"batch_key": batch_key},
            ).mappings().first()

            if existing_batch:
                print(
                    f"[generate_fresh_events] Batch already processed: "
                    f"{batch_key}. Skipping insert. "
                    f"Recorded events: {existing_batch['event_count']} "
                    f"({existing_batch['first_event_id']}-"
                    f"{existing_batch['last_event_id']})."
                )
                return

            users = conn.execute(
                text("SELECT user_id FROM raw.users")
            ).scalars().all()

            products = conn.execute(
                text("SELECT product_id FROM raw.products")
            ).scalars().all()

            if not users:
                raise RuntimeError("raw.users is empty. Load initial data first.")

            if not products:
                raise RuntimeError("raw.products is empty. Load initial data first.")

            max_event_id = conn.execute(
                text("SELECT COALESCE(MAX(event_id), 0) FROM raw.events")
            ).scalar_one()

            now = datetime.now(timezone.utc).replace(tzinfo=None)
            start = now - timedelta(hours=1)
            rng = random.Random()

            events = []

            for i in range(1, BATCH_SIZE + 1):
                event_time = start + (now - start) * rng.random()

                events.append({
                    "event_id": max_event_id + i,
                    "user_id": rng.choice(users),
                    "product_id": rng.choice(products),
                    "event_type": rng.choices(
                        EVENT_TYPES, weights=EVENT_WEIGHTS, k=1
                    )[0],
                    "timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "session_id": f"sess_{rng.randint(1, 5000)}",
                    "device": rng.choice(DEVICES),
                })

            conn.execute(
                text("""
                    INSERT INTO raw.events (
                        event_id, user_id, product_id, event_type,
                        timestamp, session_id, device
                    )
                    VALUES (
                        :event_id, :user_id, :product_id, :event_type,
                        :timestamp, :session_id, :device
                    )
                """),
                events,
            )

            conn.execute(
                text("""
                    INSERT INTO raw.ingestion_batches (
                        batch_key, first_event_id, last_event_id, event_count
                    )
                    VALUES (
                        :batch_key, :first_event_id, :last_event_id, :event_count
                    )
                """),
                {
                    "batch_key": batch_key,
                    "first_event_id": max_event_id + 1,
                    "last_event_id": max_event_id + BATCH_SIZE,
                    "event_count": BATCH_SIZE,
                },
            )

        print(f"[generate_fresh_events] Added {BATCH_SIZE} events.")
        print(f"[generate_fresh_events] Batch key: {batch_key}")
        print(
            f"[generate_fresh_events] Event IDs: "
            f"{max_event_id + 1} - {max_event_id + BATCH_SIZE}"
        )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()