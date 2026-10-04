from pathlib import Path

import pendulum
from airflow.sdk import dag, task

from orchestration.training_pipeline import (
    register_challenger,
    reproduce_training_snapshot,
    train_candidate_model,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# orchestrate snapshot, training, tracking, dan challenger registration
@dag(
    dag_id="taxi_initial_training",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    tags=["bcc", "mlops", "taxi", "training"],
)
def taxi_initial_training():
    # DVC memastikan model training dimulai dari snapshot yang reproducible
    @task
    def create_snapshot() -> dict:
        return reproduce_training_snapshot(PROJECT_ROOT)

    # MLflow nyatet baseline dan candidate model dari snapshot yang sama
    @task
    def train_model(snapshot_info: dict) -> dict:
        _ = snapshot_info
        return train_candidate_model(PROJECT_ROOT)

    # candidate yang beat baseline baru masuk registry sebagai challenger
    @task
    def register_candidate(training_result: dict) -> dict:
        return register_challenger(training_result)

    snapshot_info = create_snapshot()
    training_result = train_model(snapshot_info)
    register_candidate(training_result)


taxi_initial_training()
