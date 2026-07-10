from feast import Entity, FeatureView, Field
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource
from feast.types import Int64, Float32
from feast.value_type import ValueType
from datetime import timedelta

user = Entity(name="user_id", join_keys=["user_id"], value_type=ValueType.INT64)

user_features_source = PostgreSQLSource(
    name="mart_user_features_source",
    query="SELECT * FROM analytics.mart_user_features",  # docelowy schemat marts/analytics
    timestamp_field="event_timesta"
                    "mp",
)

user_features_view = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=90),
    schema=[
        Field(name="count_interactions_last_7_days", dtype=Int64),
        Field(name="count_clicks_last_7_days", dtype=Int64),
        Field(name="count_purchases_last_7_days", dtype=Int64),
        Field(name="avg_daily_session_duration_minutes", dtype=Float32),
    ],
    online=True,
    source=user_features_source,
)