import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pydantic import BaseModel, PositiveInt, field_validator
from sqlalchemy import create_engine, text

load_dotenv()


def require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable '{key}'.")
    return value


USER = require_env("POSTGRES_USER")
PASSWORD = require_env("POSTGRES_PASSWORD")
DB_NAME = require_env("POSTGRES_DB")
HOST = os.getenv("POSTGRES_HOST", "localhost")
PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

LOOKBACK_HOURS = int(os.getenv("VALIDATION_LOOKBACK_HOURS", "24"))


class RecentEventsCheck(BaseModel):
    row_count: PositiveInt
    earliest_timestamp: datetime
    latest_timestamp: datetime

    @field_validator("latest_timestamp")
    @classmethod
    def latest_not_before_earliest(cls, v, info):
        earliest = info.data.get("earliest_timestamp")
        if earliest is not None and v < earliest:
            raise ValueError("latest_timestamp < earliest_timestamp")
        return v


def fetch_stats(engine) -> dict:
    query = text(
        """
        SELECT COUNT(*) AS row_count,
               MIN(timestamp::timestamp) AS earliest_timestamp,
               MAX(timestamp::timestamp) AS latest_timestamp
        FROM raw.events
        WHERE timestamp::timestamp >= :cutoff
        """
    )
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    with engine.connect() as conn:
        row = conn.execute(query, {"cutoff": cutoff}).mappings().first()
    return dict(row)


def main() -> None:
    stats = fetch_stats(create_engine(DATABASE_URL))
    print(f"[validate_data] okno: {LOOKBACK_HOURS}h, wierszy: {stats['row_count']}")

    if stats["row_count"] == 0:
        print("[validate_data] BŁĄD: brak świeżych zdarzeń w raw.events.", file=sys.stderr)
        sys.exit(1)

    try:
        checked = RecentEventsCheck(**stats)
    except Exception as e:
        print(f"[validate_data] BŁĄD walidacji: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[validate_data] OK: {checked.earliest_timestamp} .. {checked.latest_timestamp}")


if __name__ == "__main__":
    main()