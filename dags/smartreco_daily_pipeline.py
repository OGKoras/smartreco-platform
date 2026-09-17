from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/opt/airflow/smartreco"

default_args = {
    "owner": "smartreco",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="smartreco_daily_pipeline",
    description="Codzienny pipeline: walidacja danych -> dbt -> Feast -> trening modelu",
    default_args=default_args,
    schedule="0 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["smartreco", "mlops"],
) as dag:

    validate_data = BashOperator(
        task_id="validate_data",
        bash_command=f"cd {PROJECT_ROOT}/src/validation && python validate_data.py",
    )

    run_dbt_transformations = BashOperator(
        task_id="run_dbt_transformations",
        bash_command=(
            f"cd {PROJECT_ROOT}/src/transform/smartreco_transform && "
            f"dbt run --profiles-dir ."
        ),
    )

    materialize_features = BashOperator(
        task_id="materialize_features",
        bash_command=(
            f"cd {PROJECT_ROOT}/src/features/feature_repo && "
            f"feast materialize-incremental $(date -u +%Y-%m-%dT%H:%M:%S)"
        ),
    )

    train_model = BashOperator(
        task_id="train_model",
        bash_command=f"cd {PROJECT_ROOT}/src/training && python train.py",
    )

    validate_data >> run_dbt_transformations >> materialize_features >> train_model