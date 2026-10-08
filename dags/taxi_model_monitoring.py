import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import Param, dag, get_current_context, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARGS = {
    "owner": "bcc",
    "retries": 0,
    "pool": "taxi_workshop",
    "execution_timeout": timedelta(minutes=30),
}


@dag(
    dag_id="taxi_model_monitoring",
    description="Memeriksa performa champion dan retraining jika kualitas menurun.",
    default_args=DEFAULT_ARGS,
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    dagrun_timeout=timedelta(hours=1),
    is_paused_upon_creation=False,
    params={
        "degradation_multiplier": Param(
            float(os.getenv("RETRAIN_MAE_MULTIPLIER", "1.25")),
            type="number",
            minimum=1.0,
        ),
        "min_samples": Param(
            int(os.getenv("RETRAIN_MIN_SAMPLES", "100")),
            type="integer",
            minimum=1,
        ),
        "recent_limit": Param(
            int(os.getenv("RETRAIN_RECENT_LIMIT", "500")),
            type="integer",
            minimum=1,
        ),
    },
    tags=["bcc", "mlops", "taxi", "monitoring"],
)
def taxi_model_monitoring():
    @task(
        task_id="evaluate_model",
        task_display_name="Mengevaluasi performa champion pada data terbaru.",
        retries=1,
        retry_delay=timedelta(seconds=30),
    )
    def evaluate_model() -> dict:
        from orchestration.monitoring_pipeline import evaluate_champion_performance

        context = get_current_context()
        params = context["params"]

        return evaluate_champion_performance(
            project_root=PROJECT_ROOT,
            degradation_multiplier=float(params["degradation_multiplier"]),
            min_samples=int(params["min_samples"]),
            recent_limit=int(params["recent_limit"]),
        )

    @task(
        task_id="maybe_retrain",
        task_display_name="Retraining hanya jika evaluasi merekomendasikannya.",
    )
    def maybe_retrain(monitoring_result: dict) -> dict:
        from orchestration.monitoring_pipeline import retrain_if_recommended

        return retrain_if_recommended(
            project_root=PROJECT_ROOT,
            monitoring_result=monitoring_result,
        )

    monitoring_result = evaluate_model()
    maybe_retrain(monitoring_result)


dag = taxi_model_monitoring()
