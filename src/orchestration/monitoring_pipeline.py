from pathlib import Path

import pandas as pd

from data_versioning.pipeline_files import read_csv_dataset, write_csv_atomic
from data_versioning.snapshot import (
    build_snapshot_name,
    create_training_snapshot,
    describe_snapshot,
)
from monitoring.performance import (
    build_evaluation_table,
    save_performance_artifacts,
    summarize_performance,
)
from monitoring.prediction_log import load_prediction_log
from monitoring.reference import get_champion_reference
from orchestration.training_pipeline import register_challenger
from training.experiment import run_mlflow_experiment


# evaluate champion prediction yang actual demand-nya sudah available
def evaluate_champion_performance(
    project_root: Path,
    degradation_multiplier: float = 1.25,
    min_samples: int = 100,
    recent_limit: int = 500,
) -> dict:
    # champion MLflow run jadi sumber reference MAE dan model version
    root = Path(project_root)
    reference = get_champion_reference()

    prediction_path = root / "data" / "monitoring" / "predictions.jsonl"
    evaluation_path = root / "data" / "monitoring" / "evaluations.csv"
    summary_path = root / "data" / "monitoring" / "performance_summary.json"
    demand_dir = root / "data" / "processed" / "demand"

    records = load_prediction_log(prediction_path)
    evaluations = build_evaluation_table(
        prediction_records=records,
        demand_dir=demand_dir,
        model_version=str(reference["model_version"]),
    )

    summary = summarize_performance(
        evaluations=evaluations,
        reference_mae=float(reference["reference_mae"]),
        degradation_multiplier=degradation_multiplier,
        min_samples=min_samples,
        recent_limit=recent_limit,
    )
    summary.update(
        {
            "model_name": reference["model_name"],
            "model_version": reference["model_version"],
            "run_id": reference["run_id"],
            "degradation_multiplier": degradation_multiplier,
            "min_samples": min_samples,
            "recent_limit": recent_limit,
        }
    )

    save_performance_artifacts(
        evaluations=evaluations,
        summary=summary,
        evaluation_path=evaluation_path,
        summary_path=summary_path,
    )

    return summary


# freeze feature dataset terbaru sampai tanggal monitoring terakhir buat retraining
def create_retraining_snapshot(
    project_root: Path,
    cutoff_date: str,
) -> dict[str, str | int]:
    # runtime retraining snapshot tetap punya nama dan sha yang jelas walaupun dibuat Airflow
    root = Path(project_root)
    feature_path = root / "data" / "features" / "taxi_demand_features.csv"

    if not feature_path.exists():
        raise FileNotFoundError(f"feature dataset belum ada: {feature_path}")

    features = read_csv_dataset(feature_path)
    snapshot = create_training_snapshot(
        features=features,
        cutoff_date=cutoff_date,
    )

    output_path = root / "data" / "snapshots" / "training" / build_snapshot_name(cutoff_date)
    write_csv_atomic(snapshot, output_path)

    return describe_snapshot(output_path)


# retrain cuma kalau monitoring memang recommend dan register hasilnya sebagai challenger
def retrain_if_recommended(
    project_root: Path,
    monitoring_result: dict,
) -> dict:
    # no degradation berarti task selesai tanpa bikin model baru
    if not bool(monitoring_result["retrain_recommended"]):
        return {
            "status": "not_needed",
            "reason": "performance_within_threshold",
        }

    latest_target = monitoring_result.get("latest_target_datetime")

    if latest_target is None:
        return {
            "status": "not_needed",
            "reason": "no_evaluated_predictions",
        }

    # cutoff retraining pakai tanggal actual terbaru yang sudah berhasil dievaluate
    cutoff_date = pd.Timestamp(latest_target).date().isoformat()
    snapshot_info = create_retraining_snapshot(
        project_root=project_root,
        cutoff_date=cutoff_date,
    )
    snapshot_path = (
        Path(project_root) / "data" / "snapshots" / "training" / str(snapshot_info["name"])
    )

    training_result = run_mlflow_experiment(
        snapshot_path=snapshot_path,
        stage="retraining-validation",
    )
    registration = register_challenger(training_result)

    return {
        "status": "retrained",
        "cutoff_date": cutoff_date,
        "snapshot_name": snapshot_info["name"],
        "dataset_sha256": snapshot_info["sha256"],
        "candidate_mae": training_result["model_mae"],
        "candidate_rmse": training_result["model_rmse"],
        "candidate_run_id": training_result["model_run_id"],
        "registration": registration,
    }
