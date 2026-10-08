"""Tracked single training and a bounded, sequential workshop parameter search."""

import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import mlflow
import pandas as pd
from threadpoolctl import threadpool_limits

from data_versioning.snapshot import describe_snapshot
from tracking.experiment_metadata import (
    log_evaluation_artifacts,
    log_experiment_metadata,
)
from tracking.mlflow_tracking import configure_mlflow, log_baseline_run, log_sklearn_run
from training.evaluate import calculate_regression_metrics, evaluate_naive_24h
from training.train import (
    DEFAULT_VALIDATION_DAYS,
    HIST_GRADIENT_BOOSTING_PARAMS,
    prepare_model_input,
    split_train_validation,
    train_hist_gradient_boosting,
)

# Three deliberate trade-offs, not a large Cartesian grid. Fit sequentially on CPU.
WORKSHOP_CONFIGURATIONS = {
    "compact": {
        "learning_rate": 0.1,
        "max_iter": 100,
        "max_leaf_nodes": 15,
        "l2_regularization": 1.0,
    },
    "balanced": {
        "learning_rate": 0.05,
        "max_iter": 200,
        "max_leaf_nodes": 31,
        "l2_regularization": 0.1,
    },
    "slow-learning": {
        "learning_rate": 0.03,
        "max_iter": 300,
        "max_leaf_nodes": 31,
        "l2_regularization": 1.0,
    },
}


def load_training_snapshot(snapshot_path: Path) -> pd.DataFrame:
    path = Path(snapshot_path)
    if not path.exists():
        raise FileNotFoundError(f"training snapshot belum ada: {path}")
    return pd.read_parquet(path)


def _run_name(label: str) -> str:
    return f"{label}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}"


def _baseline(
    snapshot_path,
    info,
    train,
    validation,
    stage,
    comparison_id,
    cpu_threads,
    validation_days,
) -> dict:
    with mlflow.start_run(run_name=_run_name("naive-24h"), nested=mlflow.active_run() is not None):
        mlflow.set_tags({"model_family": "baseline", "config_name": "baseline"})
        mlflow.log_param("model_type", "naive_24h")
        log_experiment_metadata(
            snapshot_path,
            info,
            train,
            validation,
            stage,
            comparison_id,
            cpu_threads,
            validation_days,
        )
        started = perf_counter()
        metrics = evaluate_naive_24h(validation)
        mlflow.log_metric("evaluation_seconds", perf_counter() - started)
        run_id = log_baseline_run(metrics, len(train), len(validation), info, stage)
        log_evaluation_artifacts(validation, validation["lag_24h"].to_numpy())
        return {
            "baseline_run_id": run_id,
            "baseline_mae": metrics["mae"],
            "baseline_rmse": metrics["rmse"],
        }


def _candidate(
    snapshot_path,
    info,
    train,
    validation,
    stage,
    comparison_id,
    params,
    config_name,
    cpu_threads,
    validation_days,
) -> dict:
    with mlflow.start_run(
        run_name=_run_name(f"hist-gradient-boosting-poisson_{config_name}"),
        nested=mlflow.active_run() is not None,
    ):
        mlflow.set_tags({"model_family": "gradient-boosting-poisson", "config_name": config_name})
        mlflow.log_params({"model_type": "hist_gradient_boosting_poisson", **params})
        log_experiment_metadata(
            snapshot_path,
            info,
            train,
            validation,
            stage,
            comparison_id,
            cpu_threads,
            validation_days,
        )
        # Fit, evaluation, signature inference, and logging are inside the run.
        # Exceptions propagate out of start_run(), marking this run FAILED.
        with threadpool_limits(limits=cpu_threads):
            started = perf_counter()
            model = train_hist_gradient_boosting(train, params, cpu_threads=cpu_threads)
            fit_seconds = perf_counter() - started
            mlflow.log_metrics(
                {"fit_seconds": fit_seconds, "fitted_iterations": float(model.n_iter_)}
            )
            mlflow.log_params(model.get_params())
            validation_input = prepare_model_input(validation)
            predictions = model.predict(validation_input)
            metrics = calculate_regression_metrics(validation["target_trip_count"], predictions)
            model_run = log_sklearn_run(
                model,
                params,
                metrics,
                validation_input,
                len(train),
                len(validation),
                info,
                stage,
            )
            log_evaluation_artifacts(validation, predictions)
        return {
            "model_run_id": model_run["run_id"],
            "model_uri": model_run["model_uri"],
            "model_mae": metrics["mae"],
            "model_rmse": metrics["rmse"],
            "fit_seconds": fit_seconds,
            "config_name": config_name,
            "model_params": params,
        }


def run_mlflow_experiment(
    snapshot_path: Path,
    stage: str = "validation",
    model_params: dict | None = None,
    config_name: str = "balanced",
    cpu_threads: int = 2,
    validation_days: int = DEFAULT_VALIDATION_DAYS,
) -> dict:
    """Keep the baseline/model return contract used by Airflow and registry gates."""
    if validation_days < 1 or cpu_threads < 1:
        raise ValueError("validation_days dan cpu_threads harus minimal 1")
    params = {**HIST_GRADIENT_BOOSTING_PARAMS, **(model_params or {})}
    if params["loss"] != "poisson":
        raise ValueError("experiment workshop ini menggunakan loss poisson")
    tracking = configure_mlflow()
    features = load_training_snapshot(snapshot_path)
    info = describe_snapshot(snapshot_path)
    train, validation = split_train_validation(features, validation_days)
    comparison_id = uuid4().hex
    baseline = _baseline(
        snapshot_path,
        info,
        train,
        validation,
        stage,
        comparison_id,
        cpu_threads,
        validation_days,
    )
    candidate = _candidate(
        snapshot_path,
        info,
        train,
        validation,
        stage,
        comparison_id,
        params,
        config_name,
        cpu_threads,
        validation_days,
    )
    return {
        **tracking,
        "snapshot_name": str(info["name"]),
        "dataset_sha256": str(info["sha256"]),
        "comparison_id": comparison_id,
        **baseline,
        **candidate,
        "model_beats_baseline": candidate["model_mae"] < baseline["baseline_mae"],
    }


def run_hyperparameter_search(
    snapshot_path: Path,
    stage: str = "workshop-hyperparameter-search",
    cpu_threads: int = 2,
    validation_days: int = DEFAULT_VALIDATION_DAYS,
    output_dir: Path | None = None,
) -> dict:
    """Compare exactly three model configurations against one shared baseline."""
    if validation_days < 1 or cpu_threads < 1:
        raise ValueError("validation_days dan cpu_threads harus minimal 1")
    tracking = configure_mlflow()
    features = load_training_snapshot(snapshot_path)
    info = describe_snapshot(snapshot_path)
    train, validation = split_train_validation(features, validation_days)
    with mlflow.start_run(
        run_name=_run_name("hgb-hyperparameter-search"),
        nested=mlflow.active_run() is not None,
    ) as parent:
        comparison_id = parent.info.run_id
        mlflow.set_tags({"run_role": "hyperparameter-search", "selection_metric": "mae"})
        mlflow.log_param("candidate_count", len(WORKSHOP_CONFIGURATIONS))
        log_experiment_metadata(
            snapshot_path,
            info,
            train,
            validation,
            stage,
            comparison_id,
            cpu_threads,
            validation_days,
        )
        baseline = _baseline(
            snapshot_path,
            info,
            train,
            validation,
            stage,
            comparison_id,
            cpu_threads,
            validation_days,
        )
        candidates = []
        for name, overrides in WORKSHOP_CONFIGURATIONS.items():
            params = {**HIST_GRADIENT_BOOSTING_PARAMS, **overrides}
            candidates.append(
                _candidate(
                    snapshot_path,
                    info,
                    train,
                    validation,
                    stage,
                    comparison_id,
                    params,
                    name,
                    cpu_threads,
                    validation_days,
                )
            )
        # Lowest validation MAE; use RMSE then measured fit time to break exact ties.
        best = min(
            candidates,
            key=lambda row: (row["model_mae"], row["model_rmse"], row["fit_seconds"]),
        )
        rows = [
            {
                "config_name": "baseline",
                "run_id": baseline["baseline_run_id"],
                "mae": baseline["baseline_mae"],
                "rmse": baseline["baseline_rmse"],
            }
        ]
        rows.extend(
            {
                "config_name": row["config_name"],
                "run_id": row["model_run_id"],
                "mae": row["model_mae"],
                "rmse": row["model_rmse"],
                "fit_seconds": row["fit_seconds"],
                **row["model_params"],
            }
            for row in candidates
        )
        comparison = pd.DataFrame(rows)
        improvement = baseline["baseline_mae"] - best["model_mae"]
        improvement_pct = (
            100 * improvement / baseline["baseline_mae"] if baseline["baseline_mae"] else None
        )
        selection = {
            "comparison_id": comparison_id,
            "best_config": best["config_name"],
            "best_run_id": best["model_run_id"],
            "best_model_uri": best["model_uri"],
            "best_params": best["model_params"],
            "selection_rule": "lowest validation MAE; ties: RMSE, then fit_seconds",
            "dataset_sha256": str(info["sha256"]),
            "validation_start": validation["timestamp"].min().isoformat(),
            "validation_end": validation["timestamp"].max().isoformat(),
            "baseline_mae": baseline["baseline_mae"],
            "best_mae": best["model_mae"],
            "best_rmse": best["model_rmse"],
            "mae_improvement_pct": improvement_pct,
            "model_beats_baseline": improvement > 0,
            "promotion": "manual review required; this search does not change registry aliases",
        }
        lines = [
            "# Workshop experiment comparison",
            "",
            "All candidates use the same chronological train/validation split and snapshot.",
            "",
            f"Dataset SHA256: `{info['sha256']}`",
            "",
            f"Validation: {selection['validation_start']} to {selection['validation_end']}",
            "",
            "| Configuration | MAE | RMSE | Fit seconds |",
            "| --- | ---: | ---: | ---: |",
            f"| naive-24h baseline | {baseline['baseline_mae']:.4f} | {baseline['baseline_rmse']:.4f} | n/a |",
        ]
        for row in candidates:
            lines.append(
                f"| {row['config_name']} | {row['model_mae']:.4f} | "
                f"{row['model_rmse']:.4f} | {row['fit_seconds']:.2f} |"
            )
        lines += [
            "",
            "## Selection rationale",
            "",
            f"Selected **{best['config_name']}** using lowest validation MAE, "
            "with RMSE and measured fit time as tie breakers.",
            "",
            "MAE measures average pickup-count error. RMSE highlights large misses. "
            "Fit time is a CPU cost reference, not a production latency benchmark.",
            "",
            f"Beats baseline: **{improvement > 0}**. "
            f"Absolute MAE improvement: **{improvement:.4f}**.",
            "",
            f"Best run: `{best['model_run_id']}`",
            "",
            "## Limits and next decision",
            "",
            "This is validation-based model selection, not an unbiased final test. "
            "Inspect per-zone errors and evaluate on a later untouched period before production. "
            "Each configuration changes several parameters, so this compares configurations; "
            "it does not isolate the causal effect of one hyperparameter. "
            "Training is sequential with the requested CPU thread limit. "
            "Random seed, effective estimator parameters, data hashes, and split boundaries "
            "are logged; exact equivalence across hardware is not guaranteed.",
            "",
            "If git_dirty=true, the commit alone cannot recreate local edits. "
            "Save those changes in Git before sharing a reproducibility claim.",
            "",
            "Register the selected candidate only after review. Champion is not changed here.",
        ]
        report = "\n".join(lines) + "\n"
        mlflow.log_text(comparison.to_csv(index=False), "comparison/results.csv")
        mlflow.log_text(report, "comparison/selection_report.md")
        mlflow.log_dict(selection, "comparison/selection.json")
        mlflow.log_metrics({"best_mae": best["model_mae"], "best_rmse": best["model_rmse"]})
        mlflow.set_tags({"best_run_id": best["model_run_id"], "best_config": best["config_name"]})
        client = mlflow.MlflowClient()
        for row in candidates:
            client.set_tag(row["model_run_id"], "selected_in_search", str(row is best).lower())
        destination = (
            Path(output_dir)
            if output_dir
            else Path(__file__).resolve().parents[2] / "data" / "experiments"
        ) / comparison_id
        destination.mkdir(parents=True, exist_ok=True)
        comparison.to_csv(destination / "results.csv", index=False)
        (destination / "selection_report.md").write_text(report, encoding="utf-8")
        (destination / "selection.json").write_text(
            json.dumps(selection, indent=2), encoding="utf-8"
        )
        return {
            **tracking,
            **selection,
            "parent_run_id": comparison_id,
            "report_dir": str(destination),
            "candidate_runs": candidates,
        }
