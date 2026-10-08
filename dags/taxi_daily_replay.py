from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import Param, dag, get_current_context, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARGS = {
    "owner": "bcc",
    "retries": 0,
    "pool": "taxi_workshop",
    "execution_timeout": timedelta(minutes=15),
}


@dag(
    dag_id="taxi_daily_replay",
    description="Memproses satu batch taxi historis dari data mentah sampai fitur demand.",
    default_args=DEFAULT_ARGS,
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(hours=1),
    is_paused_upon_creation=False,
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
    @task(
        task_id="get_replay_date", task_display_name="Membaca tanggal batch dari parameter trigger."
    )
    def get_replay_date() -> str:
        context = get_current_context()
        return str(context["params"]["replay_date"])

    @task(task_id="release_batch", task_display_name="Melepas batch historis ke area raw.")
    def release_batch(replay_date: str) -> dict:
        from orchestration.daily_pipeline import release_replay_batch

        return release_replay_batch(
            project_root=PROJECT_ROOT,
            replay_date=replay_date,
        )

    @task(
        task_id="validate_batch",
        task_display_name="Memeriksa isi dan kelengkapan batch.",
        retries=1,
        retry_delay=timedelta(seconds=30),
    )
    def validate_batch(
        replay_date: str,
        release_info: dict,
    ) -> dict:
        from orchestration.daily_pipeline import validate_replay_batch

        # release_info menjadi dependency metadata, bukan untuk membawa dataframe.
        _ = release_info
        return validate_replay_batch(
            project_root=PROJECT_ROOT,
            replay_date=replay_date,
        )

    @task(
        task_id="aggregate_demand",
        task_display_name="Menghitung demand per jam dari trip.",
        retries=1,
        retry_delay=timedelta(seconds=30),
    )
    def aggregate_demand(
        replay_date: str,
        validation_info: dict,
    ) -> dict:
        from orchestration.daily_pipeline import prepare_replay_demand

        _ = validation_info
        return prepare_replay_demand(
            project_root=PROJECT_ROOT,
            replay_date=replay_date,
        )

    @task(
        task_id="rebuild_features",
        task_display_name="Memeriksa cache dan menyiapkan fitur replay.",
        retries=1,
        retry_delay=timedelta(seconds=30),
    )
    def rebuild_features(
        replay_date: str,
        demand_info: dict,
    ) -> dict:
        from orchestration.daily_pipeline import rebuild_replay_features

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


dag = taxi_daily_replay()
