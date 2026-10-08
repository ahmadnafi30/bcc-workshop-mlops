from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import dag, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARGS = {
    "owner": "bcc",
    "retries": 0,
    "pool": "taxi_workshop",
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id="taxi_initial_training",
    description="Menyiapkan snapshot DVC, melatih model, dan mencatat kandidat di MLflow.",
    default_args=DEFAULT_ARGS,
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(hours=1),
    is_paused_upon_creation=False,
    tags=["bcc", "mlops", "taxi", "training"],
)
def taxi_initial_training():
    @task(
        task_id="create_snapshot",
        task_display_name="Membuat snapshot training yang reproducible.",
        retries=1,
        retry_delay=timedelta(seconds=30),
    )
    def create_snapshot() -> dict:
        from orchestration.training_pipeline import reproduce_training_snapshot

        return reproduce_training_snapshot(PROJECT_ROOT)

    @task(task_id="train_model", task_display_name="Melatih model kandidat dan mencatat metrik.")
    def train_model(snapshot_info: dict) -> dict:
        from orchestration.training_pipeline import train_candidate_model

        return train_candidate_model(PROJECT_ROOT, snapshot_info=snapshot_info)

    @task(task_id="register_candidate", task_display_name="Mendaftarkan kandidat model di MLflow.")
    def register_candidate(training_result: dict) -> dict:
        from orchestration.training_pipeline import register_challenger

        return register_challenger(training_result)

    snapshot_info = create_snapshot()
    training_result = train_model(snapshot_info)
    register_candidate(training_result)


dag = taxi_initial_training()
