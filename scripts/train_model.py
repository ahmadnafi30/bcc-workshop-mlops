import json
from pathlib import Path

import pandas as pd

from training.evaluate import (
    calculate_regression_metrics,
    evaluate_naive_24h,
)
from training.train import (
    prepare_model_input,
    save_model_bundle,
    split_train_validation,
    train_hist_gradient_boosting,
)


# load feature dataset yang sudah jadi input final untuk initial model training
def load_features(feature_path: Path) -> pd.DataFrame:
    # training sengaja gagal jelas kalau feature engineering belum dijalankan
    if not feature_path.exists():
        raise FileNotFoundError(
            f"feature dataset belum ada: {feature_path}. "
            "jalanin scripts/build_features.py dulu."
        )

    return pd.read_parquet(feature_path)


# train baseline dan model utama lalu simpan hasil evaluasinya buat comparison
def main() -> None:
    # semua artifact disimpan relatif dari root repository supaya command konsisten
    root = Path(__file__).resolve().parents[1]
    feature_path = root / "data" / "features" / "taxi_demand_features.parquet"
    model_path = root / "models" / "taxi_demand_model.joblib"
    metrics_path = root / "models" / "initial_metrics.json"

    # load feature dataset lalu bikin train-validation split berdasarkan waktu
    features = load_features(feature_path)
    train_data, validation_data = split_train_validation(features)

    # baseline 24 jam jadi patokan apakah ML model kita benar-benar ada improvement
    baseline_metrics = evaluate_naive_24h(validation_data)

    # train model utama lalu evaluate ke validation period yang sama
    model = train_hist_gradient_boosting(train_data)
    predictions = model.predict(
        prepare_model_input(validation_data)
    )
    model_metrics = calculate_regression_metrics(
        y_true=validation_data["target_trip_count"],
        y_pred=predictions,
    )

    # model bundle disimpan lokal dulu sebelum nanti pindah ke MLflow model registry
    save_model_bundle(model, model_path)

    # simpan metric dan metadata sederhana supaya hasil run tetap bisa dibandingin
    metrics = {
        "train_rows": len(train_data),
        "validation_rows": len(validation_data),
        "baseline_24h": baseline_metrics,
        "hist_gradient_boosting": model_metrics,
        "model_beats_baseline": (
            model_metrics["mae"] < baseline_metrics["mae"]
        ),
    }

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    # tampilkan comparison yang gampang dibaca langsung dari terminal
    print("\nvalidation result")
    print(
        f"naive 24h              -> "
        f"MAE {baseline_metrics['mae']:.3f}, "
        f"RMSE {baseline_metrics['rmse']:.3f}"
    )
    print(
        f"hist gradient boosting -> "
        f"MAE {model_metrics['mae']:.3f}, "
        f"RMSE {model_metrics['rmse']:.3f}"
    )
    print(
        "model beats baseline  -> "
        f"{metrics['model_beats_baseline']}"
    )
    print(f"\nmodel: {model_path}")
    print(f"metrics: {metrics_path}")


if __name__ == "__main__":
    main()
