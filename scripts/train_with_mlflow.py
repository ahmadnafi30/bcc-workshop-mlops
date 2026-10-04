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


# load snapshot yang sudah dibekukan DVC buat experiment tracking
def load_training_snapshot(snapshot_path: Path) -> pd.DataFrame:
    # kasih error yang jelas kalau snapshot belum pernah direproduce
    if not snapshot_path.exists():
        raise FileNotFoundError(
            f"training snapshot belum ada: {snapshot_path}. "
            "jalanin uv run dvc repro create_training_snapshot dulu."
        )

    return pd.read_parquet(snapshot_path)


# train baseline dan model utama lalu kirim result plus dataset fingerprint ke MLflow
def main() -> None:
    # siapin tracking server dulu sebelum kita mulai bikin experiment run
    tracking = configure_mlflow()

    root = Path(__file__).resolve().parents[1]
    snapshot_path = (
        root
        / "data"
        / "snapshots"
        / "training"
        / "taxi_demand_2025-01-26.parquet"
    )

    # dua model di run ini wajib pakai snapshot yang sama supaya comparison-nya fair
    features = load_training_snapshot(snapshot_path)
    snapshot_info = describe_snapshot(snapshot_path)
    train_data, validation_data = split_train_validation(features)

    # baseline masuk MLflow sebagai run sendiri dan tetap dicatat dataset version-nya
    baseline_metrics = evaluate_naive_24h(validation_data)
    baseline_run_id = log_baseline_run(
        metrics=baseline_metrics,
        train_rows=len(train_data),
        validation_rows=len(validation_data),
        dataset_info=snapshot_info,
    )

    # train gradient boosting lalu evaluate pada validation period yang sama
    model = train_hist_gradient_boosting(train_data)
    validation_input = prepare_model_input(validation_data)
    predictions = model.predict(validation_input)
    model_metrics = calculate_regression_metrics(
        y_true=validation_data["target_trip_count"],
        y_pred=predictions,
    )

    # model artifact dan dataset fingerprint dilog dalam experiment run yang sama
    model_run = log_sklearn_run(
        model=model,
        model_params=HIST_GRADIENT_BOOSTING_PARAMS,
        metrics=model_metrics,
        input_example=validation_input,
        train_rows=len(train_data),
        validation_rows=len(validation_data),
        dataset_info=snapshot_info,
    )

    # summary terminal nunjukin experiment result sekaligus dataset version yang dipakai
    print("\nmlflow experiment selesai")
    print(f"tracking uri: {tracking['tracking_uri']}")
    print(f"experiment: {tracking['experiment_name']}")
    print(f"snapshot: {snapshot_info['name']}")
    print(f"dataset sha256: {snapshot_info['sha256']}")
    print(
        f"baseline -> MAE {baseline_metrics['mae']:.3f}, "
        f"run {baseline_run_id}"
    )
    print(
        f"model    -> MAE {model_metrics['mae']:.3f}, "
        f"run {model_run['run_id']}"
    )
    print(f"model uri: {model_run['model_uri']}")


if __name__ == "__main__":
    main()
