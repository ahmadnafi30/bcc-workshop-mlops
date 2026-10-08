import logging
import os
import subprocess
import sys
from pathlib import Path

from data_versioning.pipeline_config import training_snapshot_path
from data_versioning.snapshot import calculate_file_sha256, describe_snapshot
from tracking.mlflow_tracking import configure_mlflow
from tracking.model_registry import register_run_model
from training.experiment import run_mlflow_experiment

DEFAULT_SNAPSHOT_NAME = "taxi_demand_2025-01-26.parquet"
LOGGER = logging.getLogger(__name__)


# reproduce DVC stage supaya training selalu mulai dari snapshot yang jelas
def reproduce_training_snapshot(
    project_root: Path,
) -> dict[str, str | int]:
    # DVC executable berasal dari uv environment yang sama dengan Airflow
    root = Path(project_root)
    env = os.environ.copy()
    # dvc.yaml uses `python`; make it the same environment as this task/CLI.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "dvc", "repro", "create_training_snapshot"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        env=env,
    )
    if result.stdout.strip():
        LOGGER.info("DVC reproduction:\n%s", result.stdout.strip())
    if result.returncode:
        raise RuntimeError(
            f"DVC reproduction gagal:\n{result.stderr.strip()}\n{result.stdout.strip()}"
        )
    snapshot_path = training_snapshot_path(root)
    return {**describe_snapshot(snapshot_path), "path": str(snapshot_path)}


# train baseline dan candidate model dari DVC snapshot lalu log semuanya ke MLflow
def train_candidate_model(
    project_root: Path,
    snapshot_info: dict | None = None,
) -> dict[str, str | float | bool]:
    # training function reuse flow yang sama dengan scripts/train_with_mlflow.py
    snapshot_path = training_snapshot_path(project_root)
    if snapshot_info is not None:
        name = str(snapshot_info["name"])
        if Path(name).name != name:
            raise ValueError("snapshot name harus berupa nama file")
        snapshot_path = Path(project_root) / "data/snapshots/training" / name
        if calculate_file_sha256(snapshot_path) != snapshot_info["sha256"]:
            raise ValueError(
                "snapshot berubah setelah task create_snapshot; reproduce ulang sebelum training"
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
