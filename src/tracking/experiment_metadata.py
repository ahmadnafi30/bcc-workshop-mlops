"""Dataset, code, and evaluation artifacts for classical ML experiment runs."""

import subprocess
from hashlib import sha256
from html import escape
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd

from features.build_features import MODEL_FEATURE_COLUMNS
from tracking.mlflow_tracking import build_dataset_params


def log_experiment_metadata(
    snapshot_path: Path,
    dataset_info: dict,
    train_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    stage: str,
    comparison_id: str,
    cpu_threads: int,
    validation_days: int,
) -> None:
    """Log provenance before fit so failed runs keep their configuration."""
    root = Path(__file__).resolve().parents[2]
    mlflow.log_params(
        {
            **build_dataset_params(dataset_info),
            "train_rows": len(train_data),
            "validation_rows": len(validation_data),
            "train_start": train_data["timestamp"].min().isoformat(),
            "train_end": train_data["timestamp"].max().isoformat(),
            "validation_start": validation_data["timestamp"].min().isoformat(),
            "validation_end": validation_data["timestamp"].max().isoformat(),
            "validation_days": validation_days,
            "split_strategy": "chronological_last_days",
            "cpu_threads": cpu_threads,
            "forecast_horizon": "1h",
        }
    )
    tags = {
        "task": "taxi-demand-forecasting",
        "stage": stage,
        "comparison_id": comparison_id,
        "dataset_version": str(dataset_info["sha256"]),
    }
    # A Docker image may not contain .git; explicitly record missing provenance.
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=normal"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        tags.update({"mlflow.source.git.commit": commit, "git_dirty": str(bool(status)).lower()})
    except (OSError, subprocess.SubprocessError):
        tags["git_revision_status"] = "unavailable"
    mlflow.set_tags(tags)
    for filename in ["dvc.lock", "dvc.yaml", "params.json", "uv.lock"]:
        path = root / filename
        if path.exists():
            mlflow.log_param(
                filename.replace(".", "_") + "_sha256",
                sha256(path.read_bytes()).hexdigest(),
            )
            mlflow.log_artifact(str(path), artifact_path="lineage")
    mlflow.log_dict(
        {
            "features": MODEL_FEATURE_COLUMNS,
            "target": "target_trip_count",
            "dataset_sha256": dataset_info["sha256"],
            "split_strategy": "chronological_last_days",
        },
        "lineage/feature_schema.json",
    )
    for context, frame in [("training", train_data), ("validation", validation_data)]:
        dataset = mlflow.data.from_pandas(
            frame[MODEL_FEATURE_COLUMNS + ["target_trip_count"]],
            source=str(snapshot_path.resolve()),
            name=f"{snapshot_path.stem}-{context}",
            targets="target_trip_count",
        )
        mlflow.log_input(dataset, context=context)


def log_evaluation_artifacts(validation: pd.DataFrame, predictions) -> None:
    """Keep row-level evidence and small SVG charts without extra dependencies."""
    report = validation[["timestamp", "zone_id", "target_trip_count"]].copy()
    report["prediction"] = np.asarray(predictions)
    report["residual"] = report["target_trip_count"] - report["prediction"]
    report["absolute_error"] = report["residual"].abs()
    mlflow.log_text(report.to_csv(index=False), "evaluation/predictions.csv")
    by_zone = report.groupby("zone_id")["absolute_error"].agg(["mean", "count"])
    mlflow.log_text(by_zone.to_csv(), "evaluation/error_by_zone.csv")
    # Aggregate across zones, then show up to 240 validation hours.
    hourly = report.groupby("timestamp")[["target_trip_count", "prediction"]].sum().head(240)
    maximum = max(float(hourly.max().max()), 1.0)
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="320" viewBox="0 0 800 320">',
        '<rect width="800" height="320" fill="white"/>',
        '<text x="40" y="25" font-family="sans-serif">Validation demand: actual (blue), prediction (orange)</text>',
        '<path d="M40 45V275H760" fill="none" stroke="#555"/>',
    ]
    for column, color in [("target_trip_count", "#2563eb"), ("prediction", "#ea580c")]:
        points = " ".join(
            f"{40 + i * 720 / max(len(hourly) - 1, 1):.1f},{275 - float(value) * 220 / maximum:.1f}"
            for i, value in enumerate(hourly[column])
        )
        svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')
    svg.append(
        f'<text x="40" y="305" font-family="sans-serif" font-size="12">'
        f"{escape(str(hourly.index.min()))} to {escape(str(hourly.index.max()))}; "
        f"peak scale {maximum:.0f} pickups/hour, summed over zones</text></svg>"
    )
    mlflow.log_text("".join(svg), "evaluation/actual_vs_prediction.svg")
    counts, edges = np.histogram(report["residual"], bins=30)
    peak = max(int(counts.max()), 1)
    bars = "".join(
        f'<rect x="{40 + i * 24}" y="{275 - count * 220 / peak:.1f}" '
        f'width="22" height="{count * 220 / peak:.1f}" fill="#2563eb"/>'
        for i, count in enumerate(counts)
    )
    histogram = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="320">'
        '<rect width="800" height="320" fill="white"/>'
        '<text x="40" y="25" font-family="sans-serif">Residual distribution: actual minus prediction</text>'
        f'{bars}<text x="40" y="305" font-family="sans-serif">'
        f"Residual range: {edges[0]:.1f} to {edges[-1]:.1f}; peak bin: {peak} rows</text></svg>"
    )
    mlflow.log_text(histogram, "evaluation/residual_distribution.svg")
