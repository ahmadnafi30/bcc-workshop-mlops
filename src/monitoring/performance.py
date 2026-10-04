import json
from pathlib import Path

import numpy as np
import pandas as pd


# load satu daily ground truth file dan rapihin key buat join ke prediction
def load_daily_ground_truth(
    demand_dir: Path,
    target_date,
) -> pd.DataFrame | None:
    # satu tanggal cukup dibaca sekali walaupun prediction-nya banyak zone dan jam
    path = Path(demand_dir) / f"{target_date.isoformat()}.parquet"

    if not path.exists():
        return None

    demand = pd.read_parquet(
        path,
        columns=["timestamp", "zone_id", "trip_count"],
    )
    demand["timestamp"] = pd.to_datetime(demand["timestamp"], errors="raise")

    return demand.rename(
        columns={
            "timestamp": "target_datetime",
            "trip_count": "actual_trip_count",
        }
    )


# pasangkan prediction dengan actual demand yang sudah tersedia
def build_evaluation_table(
    prediction_records: list[dict],
    demand_dir: Path,
    model_version: str | None = None,
) -> pd.DataFrame:
    # prediction kosong berarti belum ada yang bisa dievaluate
    predictions = pd.DataFrame(prediction_records)

    if predictions.empty:
        return pd.DataFrame()

    predictions["target_datetime"] = pd.to_datetime(
        predictions["target_datetime"],
        errors="raise",
    )
    predictions["logged_at"] = pd.to_datetime(
        predictions["logged_at"],
        errors="raise",
        utc=True,
    )

    if model_version is not None:
        predictions = predictions.loc[
            predictions["model_version"].astype(str) == str(model_version)
        ].copy()

    # duplicate request target yang sama cukup pakai prediction terakhir
    predictions = (
        predictions.sort_values("logged_at")
        .drop_duplicates(
            ["zone_id", "target_datetime", "model_version"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    if predictions.empty:
        return pd.DataFrame()

    predictions["target_date"] = predictions["target_datetime"].dt.date
    evaluated_days = []

    # setiap daily parquet dibaca sekali lalu join semua prediction pada tanggal itu
    for target_date, daily_predictions in predictions.groupby("target_date"):
        ground_truth = load_daily_ground_truth(
            demand_dir=demand_dir,
            target_date=target_date,
        )

        if ground_truth is None:
            continue

        evaluated_days.append(
            daily_predictions.merge(
                ground_truth,
                on=["target_datetime", "zone_id"],
                how="inner",
            )
        )

    if not evaluated_days:
        return pd.DataFrame()

    evaluations = pd.concat(evaluated_days, ignore_index=True)

    # error detail disimpan supaya summary dan debugging pakai source yang sama
    error = (
        evaluations["predicted_trip_count"]
        - evaluations["actual_trip_count"]
    )
    evaluations["absolute_error"] = error.abs()
    evaluations["squared_error"] = error**2

    return evaluations[
        [
            "logged_at",
            "target_datetime",
            "zone_id",
            "model_name",
            "model_version",
            "run_id",
            "predicted_trip_count",
            "actual_trip_count",
            "absolute_error",
            "squared_error",
        ]
    ].sort_values(
        ["target_datetime", "zone_id"]
    ).reset_index(drop=True)


# hitung recent model performance dan decide apakah retraining sudah layak dipicu
def summarize_performance(
    evaluations: pd.DataFrame,
    reference_mae: float,
    degradation_multiplier: float = 1.25,
    min_samples: int = 100,
    recent_limit: int = 500,
) -> dict[str, float | int | bool | str | None]:
    # belum cukup sample berarti belum boleh ambil keputusan retraining
    if evaluations.empty:
        return {
            "evaluation_count": 0,
            "recent_mae": None,
            "recent_rmse": None,
            "reference_mae": float(reference_mae),
            "threshold_mae": float(reference_mae * degradation_multiplier),
            "retrain_recommended": False,
            "latest_target_datetime": None,
        }

    recent = (
        evaluations.sort_values("target_datetime")
        .tail(recent_limit)
        .copy()
    )

    recent_mae = float(recent["absolute_error"].mean())
    recent_rmse = float(np.sqrt(recent["squared_error"].mean()))
    threshold_mae = float(reference_mae * degradation_multiplier)

    return {
        "evaluation_count": len(recent),
        "recent_mae": recent_mae,
        "recent_rmse": recent_rmse,
        "reference_mae": float(reference_mae),
        "threshold_mae": threshold_mae,
        "retrain_recommended": (
            len(recent) >= min_samples
            and recent_mae > threshold_mae
        ),
        "latest_target_datetime": (
            recent["target_datetime"].max().isoformat()
        ),
    }


# simpan evaluation detail dan summary supaya airflow, prometheus, dan manusia baca source yang sama
def save_performance_artifacts(
    evaluations: pd.DataFrame,
    summary: dict,
    evaluation_path: Path,
    summary_path: Path,
) -> None:
    # detail prediction disimpan parquet, sedangkan summary kecil cukup json
    evaluation_path = Path(evaluation_path)
    summary_path = Path(summary_path)
    evaluation_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    if evaluations.empty:
        pd.DataFrame(
            columns=[
                "logged_at",
                "target_datetime",
                "zone_id",
                "model_name",
                "model_version",
                "run_id",
                "predicted_trip_count",
                "actual_trip_count",
                "absolute_error",
                "squared_error",
            ]
        ).to_parquet(evaluation_path, index=False)
    else:
        evaluations.to_parquet(evaluation_path, index=False)

    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
