import os
from pathlib import Path

import pendulum
from airflow.sdk import Param, dag, get_current_context, task

from orchestration.monitoring_pipeline import (
    evaluate_champion_performance,
    retrain_if_recommended,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# evaluate champion performance dan retrain kalau recent error sudah melewati threshold
@dag(
    dag_id="taxi_model_monitoring",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
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
    # baca monitoring config dari trigger form supaya threshold gampang dieksperimenkan
    @task
    def evaluate_model() -> dict:
        context = get_current_context()
        params = context["params"]

        return evaluate_champion_performance(
            project_root=PROJECT_ROOT,
            degradation_multiplier=float(
                params["degradation_multiplier"]
            ),
            min_samples=int(params["min_samples"]),
            recent_limit=int(params["recent_limit"]),
        )

    # function ini no-op kalau monitoring masih bilang model sehat
    @task
    def maybe_retrain(monitoring_result: dict) -> dict:
        return retrain_if_recommended(
            project_root=PROJECT_ROOT,
            monitoring_result=monitoring_result,
        )

    monitoring_result = evaluate_model()
    maybe_retrain(monitoring_result)


taxi_model_monitoring()
