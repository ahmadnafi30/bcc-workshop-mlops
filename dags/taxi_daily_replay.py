from pathlib import Path

import pendulum
from airflow.sdk import Param, dag, get_current_context, task

from orchestration.daily_pipeline import (
    prepare_replay_demand,
    rebuild_replay_features,
    release_replay_batch,
    validate_replay_batch,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# orchestrate satu historical production day dari raw batch sampai feature dataset
@dag(
    dag_id="taxi_daily_replay",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    params={
        "replay_date": Param(
            "2025-01-27",
            type="string",
            format="date",
        )
    },
    tags=["bcc", "mlops", "taxi", "data"],
)
def taxi_daily_replay():
    # ambil replay date dari form trigger Airflow supaya satu DAG bisa dipakai berkali-kali
    @task
    def get_replay_date() -> str:
        context = get_current_context()
        return str(context["params"]["replay_date"])

    # release data historical seolah-olah batch baru baru saja datang
    @task
    def release_batch(replay_date: str) -> dict:
        return release_replay_batch(
            project_root=PROJECT_ROOT,
            replay_date=replay_date,
        )

    # validasi batch sebelum lanjut ke transformation
    @task
    def validate_batch(
        replay_date: str,
        release_info: dict,
    ) -> dict:
        # release_info dipakai sebagai dependency metadata, bukan buat bawa dataframe
        _ = release_info
        return validate_replay_batch(
            project_root=PROJECT_ROOT,
            replay_date=replay_date,
        )

    # aggregate trip-level batch jadi hourly demand per zone
    @task
    def aggregate_demand(
        replay_date: str,
        validation_info: dict,
    ) -> dict:
        _ = validation_info
        return prepare_replay_demand(
            project_root=PROJECT_ROOT,
            replay_date=replay_date,
        )

    # rebuild features sampai tanggal terbaru setelah processed demand tersedia
    @task
    def rebuild_features(
        replay_date: str,
        demand_info: dict,
    ) -> dict:
        _ = demand_info
        return rebuild_replay_features(
            project_root=PROJECT_ROOT,
            replay_date=replay_date,
        )

    replay_date = get_replay_date()
    release_info = release_batch(replay_date)
    validation_info = validate_batch(replay_date, release_info)
    demand_info = aggregate_demand(replay_date, validation_info)
    rebuild_features(replay_date, demand_info)


taxi_daily_replay()
