from pathlib import Path

import pandas as pd

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


# load feature dataset yang bakal dipakai untuk experiment tracking
def load_features(feature_path: Path) -> pd.DataFrame:
    # kasih error yang jelas kalau feature engineering belum pernah dijalankan
    if not feature_path.exists():
        raise FileNotFoundError(
            f"feature dataset belum ada: {feature_path}. "
            "jalanin scripts/build_features.py dulu."
        )

    return pd.read_parquet(feature_path)


# train baseline dan model utama lalu kirim semua hasilnya ke MLflow
def main() -> None:
    # siapin tracking server dulu sebelum kita mulai bikin experiment run
    tracking = configure_mlflow()

    root = Path(__file__).resolve().parents[1]
    feature_path = root / "data" / "features" / "taxi_demand_features.parquet"

    # split-nya tetap sama dengan manual training supaya comparison-nya fair
    features = load_features(feature_path)
    train_data, validation_data = split_train_validation(features)

    # baseline masuk MLflow sebagai run sendiri walaupun nggak punya trained model artifact
    baseline_metrics = evaluate_naive_24h(validation_data)
    baseline_run_id = log_baseline_run(
        metrics=baseline_metrics,
        train_rows=len(train_data),
        validation_rows=len(validation_data),
    )

    # train gradient boosting lalu evaluate pada validation period yang sama
    model = train_hist_gradient_boosting(train_data)
    validation_input = prepare_model_input(validation_data)
    predictions = model.predict(validation_input)
    model_metrics = calculate_regression_metrics(
        y_true=validation_data["target_trip_count"],
        y_pred=predictions,
    )

    # trained model ikut dilog supaya nanti run ini bisa masuk ke model registry
    model_run = log_sklearn_run(
        model=model,
        model_params=HIST_GRADIENT_BOOSTING_PARAMS,
        metrics=model_metrics,
        input_example=validation_input,
        train_rows=len(train_data),
        validation_rows=len(validation_data),
    )

    # summary terminal cukup nunjukin hasil penting dan id yang bakal dipakai next step
    print("\nmlflow experiment selesai")
    print(f"tracking uri: {tracking['tracking_uri']}")
    print(f"experiment: {tracking['experiment_name']}")
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
