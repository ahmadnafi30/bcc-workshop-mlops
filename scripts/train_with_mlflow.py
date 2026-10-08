import argparse
import json
import os
from pathlib import Path

from data_versioning.pipeline_config import training_snapshot_path
from training.experiment import run_hyperparameter_search, run_mlflow_experiment


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("nilai harus minimal 1")
    return number


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Track taxi training or compare three CPU-friendly configurations"
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="compare compact, balanced, and slow-learning",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="snapshot path; default mengikuti training_cutoff pada params.json",
    )
    parser.add_argument("--tracking-uri", help="MLflow endpoint, e.g. http://127.0.0.1:5000")
    parser.add_argument("--experiment-name", help="override MLFLOW_EXPERIMENT_NAME")
    parser.add_argument("--validation-days", type=positive_int, default=5)
    parser.add_argument("--cpu-threads", type=positive_int, default=2)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="search reports directory; each search gets a run-ID subfolder",
    )
    parser.add_argument(
        "--config-name",
        default="custom",
        help="label for a single customized configuration",
    )
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--max-iter", type=positive_int)
    parser.add_argument("--max-leaf-nodes", type=positive_int)
    parser.add_argument("--l2-regularization", type=float)
    args = parser.parse_args()
    if args.snapshot is None:
        args.snapshot = training_snapshot_path(root)
    overrides = [
        args.learning_rate,
        args.max_iter,
        args.max_leaf_nodes,
        args.l2_regularization,
    ]
    if args.search and any(value is not None for value in overrides):
        parser.error(
            "--search memakai tiga konfigurasi tetap; hyperparameter flags untuk single run"
        )
    if args.output_dir is not None and not args.search:
        parser.error("--output-dir digunakan bersama --search")
    if args.learning_rate is not None and args.learning_rate <= 0:
        parser.error("--learning-rate harus > 0")
    if args.l2_regularization is not None and args.l2_regularization < 0:
        parser.error("--l2-regularization harus >= 0")
    if args.max_leaf_nodes is not None and args.max_leaf_nodes < 2:
        parser.error("--max-leaf-nodes harus >= 2")
    return args


def main() -> None:
    args = parse_args()
    if args.tracking_uri:
        os.environ["MLFLOW_TRACKING_URI"] = args.tracking_uri
    if args.experiment_name:
        os.environ["MLFLOW_EXPERIMENT_NAME"] = args.experiment_name
    common = {
        "snapshot_path": args.snapshot,
        "cpu_threads": args.cpu_threads,
        "validation_days": args.validation_days,
    }
    if args.search:
        result = run_hyperparameter_search(**common, output_dir=args.output_dir)
    else:
        params = {
            key: value
            for key, value in {
                "learning_rate": args.learning_rate,
                "max_iter": args.max_iter,
                "max_leaf_nodes": args.max_leaf_nodes,
                "l2_regularization": args.l2_regularization,
            }.items()
            if value is not None
        }
        result = run_mlflow_experiment(
            **common,
            stage="initial-validation",
            model_params=params,
            config_name=args.config_name if params else "balanced",
        )
    print("\nMLflow experiment selesai")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
