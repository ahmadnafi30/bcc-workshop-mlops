import os

import mlflow
import mlflow.sklearn
import pandas as pd

DEFAULT_TRACKING_URI = "http://127.0.0.1:5000"
DEFAULT_EXPERIMENT_NAME = "taxi-demand-forecasting"
MODEL_ARTIFACT_NAME = "model"


# set tracking server dan experiment yang bakal dipakai semua training run
def configure_mlflow(
    tracking_uri: str | None = None,
    experiment_name: str | None = None,
) -> dict[str, str]:
    # env variable bisa override default tanpa perlu ubah code workshop
    resolved_tracking_uri = (
        tracking_uri
        or os.getenv("MLFLOW_TRACKING_URI")
        or DEFAULT_TRACKING_URI
    )
    resolved_experiment_name = (
        experiment_name
        or os.getenv("MLFLOW_EXPERIMENT_NAME")
        or DEFAULT_EXPERIMENT_NAME
    )

    # semua run setelah ini bakal masuk ke server dan experiment yang sama
    mlflow.set_tracking_uri(resolved_tracking_uri)
    experiment = mlflow.set_experiment(resolved_experiment_name)

    return {
        "tracking_uri": resolved_tracking_uri,
        "experiment_name": resolved_experiment_name,
        "experiment_id": experiment.experiment_id,
    }


# rapihin metadata snapshot jadi parameter yang gampang dibandingin antar MLflow run
def build_dataset_params(
    dataset_info: dict[str, str | int],
) -> dict[str, str | int]:
    # fingerprint dan nama snapshot jadi penghubung antara DVC dataset dan MLflow run
    return {
        "dataset_snapshot": dataset_info["name"],
        "dataset_sha256": dataset_info["sha256"],
        "dataset_rows": dataset_info["rows"],
        "dataset_zones": dataset_info["zones"],
        "dataset_start": dataset_info["start_timestamp"],
        "dataset_end": dataset_info["end_timestamp"],
    }


# log naive 24h sebagai experiment run biar baseline ikut muncul di MLflow UI
def log_baseline_run(
    metrics: dict[str, float],
    train_rows: int,
    validation_rows: int,
    dataset_info: dict[str, str | int],
) -> str:
    # baseline nggak punya artifact model karena prediction-nya langsung dari lag_24h
    with mlflow.start_run(run_name="naive-24h") as run:
        mlflow.log_params(
            {
                "model_type": "naive_24h",
                "forecast_horizon": "1h",
                "train_rows": train_rows,
                "validation_rows": validation_rows,
                **build_dataset_params(dataset_info),
            }
        )
        mlflow.log_metrics(metrics)
        mlflow.set_tags(
            {
                "task": "taxi-demand-forecasting",
                "model_family": "baseline",
                "stage": "initial-validation",
            }
        )

        return run.info.run_id


# log sklearn model lengkap dengan params, metrics, signature, dan model artifact
def log_sklearn_run(
    model,
    model_params: dict,
    metrics: dict[str, float],
    input_example: pd.DataFrame,
    train_rows: int,
    validation_rows: int,
    dataset_info: dict[str, str | int],
) -> dict[str, str]:
    # model example cukup beberapa row karena tujuannya buat schema dan contoh input
    example = input_example.head(5).copy()

    with mlflow.start_run(run_name="hist-gradient-boosting") as run:
        # params model dan dataset disimpan bareng supaya run bisa direproduce lagi
        mlflow.log_params(
            {
                "model_type": "hist_gradient_boosting",
                "categorical_feature": "zone_id",
                "forecast_horizon": "1h",
                "train_rows": train_rows,
                "validation_rows": validation_rows,
                **model_params,
                **build_dataset_params(dataset_info),
            }
        )
        mlflow.log_metrics(metrics)
        mlflow.set_tags(
            {
                "task": "taxi-demand-forecasting",
                "model_family": "gradient-boosting",
                "stage": "initial-validation",
            }
        )

        # input_example bikin MLflow nyimpen contoh input sekaligus infer model signature
        mlflow.sklearn.log_model(
            sk_model=model,
            name=MODEL_ARTIFACT_NAME,
            input_example=example,
        )

        return {
            "run_id": run.info.run_id,
            "model_uri": f"runs:/{run.info.run_id}/{MODEL_ARTIFACT_NAME}",
        }
