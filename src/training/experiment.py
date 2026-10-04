from pathlib import Path

import pandas as pd

from data_versioning.snapshot import describe_snapshot
from tracking.mlflow_tracking import (
    configure_mlflow,
    log_baseline_run,
    log_sklearn_run,
)
from training.evaluate import (
    calculate_regression_metrics,
    evaluate_naive_24h,
)
from training.train import (
    HIST_GRADIENT_BOOSTING_PARAMS,
    prepare_model_input,
    split_train_validation,
    train_hist_gradient_boosting,
)


# load snapshot yang sudah dibekukan sebelum experiment dijalankan
def load_training_snapshot(snapshot_path: Path) -> pd.DataFrame:
    # training harus fail jelas kalau snapshot belum pernah dibuat
    snapshot_path = Path(snapshot_path)

    if not snapshot_path.exists():
        raise FileNotFoundError(
            f"training snapshot belum ada: {snapshot_path}"
        )

    return pd.read_parquet(snapshot_path)


# jalanin baseline dan model utama lalu log dua-duanya ke MLflow
def run_mlflow_experiment(
    snapshot_path: Path,
) -> dict[str, str | float | bool]:
    # semua run diarahkan ke experiment yang sama sebelum training dimulai
    tracking = configure_mlflow()

    # dua model wajib pakai snapshot dan validation split yang sama supaya fair
    features = load_training_snapshot(snapshot_path)
    snapshot_info = describe_snapshot(snapshot_path)
    train_data, validation_data = split_train_validation(features)

    # baseline tetap dilog sebagai run sendiri supaya comparison muncul di MLflow UI
    baseline_metrics = evaluate_naive_24h(validation_data)
    baseline_run_id = log_baseline_run(
        metrics=baseline_metrics,
        train_rows=len(train_data),
        validation_rows=len(validation_data),
        dataset_info=snapshot_info,
    )

    # model utama ditrain dan dievaluate pada validation period yang sama
    model = train_hist_gradient_boosting(train_data)
    validation_input = prepare_model_input(validation_data)
    predictions = model.predict(validation_input)
    model_metrics = calculate_regression_metrics(
        y_true=validation_data["target_trip_count"],
        y_pred=predictions,
    )

    model_run = log_sklearn_run(
        model=model,
        model_params=HIST_GRADIENT_BOOSTING_PARAMS,
        metrics=model_metrics,
        input_example=validation_input,
        train_rows=len(train_data),
        validation_rows=len(validation_data),
        dataset_info=snapshot_info,
    )

    return {
        "tracking_uri": tracking["tracking_uri"],
        "experiment_name": tracking["experiment_name"],
        "snapshot_name": str(snapshot_info["name"]),
        "dataset_sha256": str(snapshot_info["sha256"]),
        "baseline_run_id": baseline_run_id,
        "baseline_mae": baseline_metrics["mae"],
        "baseline_rmse": baseline_metrics["rmse"],
        "model_run_id": model_run["run_id"],
        "model_uri": model_run["model_uri"],
        "model_mae": model_metrics["mae"],
        "model_rmse": model_metrics["rmse"],
        "model_beats_baseline": (
            model_metrics["mae"] < baseline_metrics["mae"]
        ),
    }
