import json
from pathlib import Path

import pandas as pd

from data_versioning.pipeline_config import training_snapshot_path
from data_versioning.pipeline_files import read_csv_dataset
from data_versioning.snapshot import describe_snapshot
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


# load training snapshot yang sudah dibekukan sebelum model training jalan
def load_training_snapshot(snapshot_path: Path) -> pd.DataFrame:
    # training harus gagal jelas kalau snapshot DVC belum pernah dibuat
    if not snapshot_path.exists():
        raise FileNotFoundError(
            f"training snapshot belum ada: {snapshot_path}. "
            "jalanin uv run dvc repro create_training_snapshot dulu."
        )

    return read_csv_dataset(snapshot_path)


# train baseline dan model utama dari snapshot yang sama lalu simpan hasil evaluasinya
def main() -> None:
    # semua artifact disimpan relatif dari root repository supaya command konsisten
    root = Path(__file__).resolve().parents[1]
    snapshot_path = training_snapshot_path(root)
    model_path = root / "models" / "taxi_demand_model.joblib"
    metrics_path = root / "models" / "initial_metrics.json"

    # load snapshot dan simpan fingerprint dataset yang benar-benar dipakai training
    features = load_training_snapshot(snapshot_path)
    snapshot_info = describe_snapshot(snapshot_path)
    train_data, validation_data = split_train_validation(features)

    # baseline 24 jam jadi patokan apakah ML model kita benar-benar ada improvement
    baseline_metrics = evaluate_naive_24h(validation_data)

    # train model utama lalu evaluate ke validation period yang sama
    model = train_hist_gradient_boosting(train_data)
    predictions = model.predict(prepare_model_input(validation_data))
    model_metrics = calculate_regression_metrics(
        y_true=validation_data["target_trip_count"],
        y_pred=predictions,
    )

    # model bundle disimpan lokal dulu sebelum nanti pindah penuh ke MLflow registry
    save_model_bundle(model, model_path)

    # dataset fingerprint ikut disimpan supaya result manual tetap reproducible
    metrics = {
        "dataset": snapshot_info,
        "train_rows": len(train_data),
        "validation_rows": len(validation_data),
        "baseline_24h": baseline_metrics,
        "hist_gradient_boosting": model_metrics,
        "model_beats_baseline": (model_metrics["mae"] < baseline_metrics["mae"]),
    }

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    # tampilkan comparison dan dataset fingerprint yang dipakai run ini
    print("\nvalidation result")
    print(f"snapshot: {snapshot_info['name']}")
    print(f"dataset sha256: {snapshot_info['sha256']}")
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
    print(f"model beats baseline  -> {metrics['model_beats_baseline']}")
    print(f"\nmodel: {model_path}")
    print(f"metrics: {metrics_path}")


if __name__ == "__main__":
    main()
