import subprocess
from pathlib import Path

from data_versioning.snapshot import describe_snapshot
from tracking.mlflow_tracking import configure_mlflow
from tracking.model_registry import register_run_model
from training.experiment import run_mlflow_experiment

DEFAULT_SNAPSHOT_NAME = "taxi_demand_2025-01-26.parquet"


# reproduce DVC stage supaya training selalu mulai dari snapshot yang jelas
def reproduce_training_snapshot(
    project_root: Path,
) -> dict[str, str | int]:
    # DVC executable berasal dari uv environment yang sama dengan Airflow
    root = Path(project_root)
    subprocess.run(
        ["dvc", "repro", "create_training_snapshot"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    snapshot_path = (
        root
        / "data"
        / "snapshots"
        / "training"
        / DEFAULT_SNAPSHOT_NAME
    )

    return describe_snapshot(snapshot_path)


# train baseline dan candidate model dari DVC snapshot lalu log semuanya ke MLflow
def train_candidate_model(
    project_root: Path,
) -> dict[str, str | float | bool]:
    # training function reuse flow yang sama dengan scripts/train_with_mlflow.py
    snapshot_path = (
        Path(project_root)
        / "data"
        / "snapshots"
        / "training"
        / DEFAULT_SNAPSHOT_NAME
    )

    return run_mlflow_experiment(
        snapshot_path,
        stage="initial-validation",
    )


# register candidate hanya kalau MAE model lebih baik daripada naive baseline
def register_challenger(
    training_result: dict[str, str | float | bool],
) -> dict[str, str]:
    # baseline gate mencegah model yang jelas lebih jelek masuk sebagai challenger
    if not bool(training_result["model_beats_baseline"]):
        return {
            "status": "not_registered",
            "reason": "model_did_not_beat_baseline",
            "run_id": str(training_result["model_run_id"]),
        }

    # registry client harus diarahkan ke tracking server yang sama dengan training run
    configure_mlflow()
    result = register_run_model(
        run_id=str(training_result["model_run_id"]),
        alias="challenger",
    )

    return {
        "status": "registered",
        **result,
    }
