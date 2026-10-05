import argparse
from pathlib import Path

from monitoring.performance import (
    build_evaluation_table,
    save_performance_artifacts,
    summarize_performance,
)
from monitoring.prediction_log import load_prediction_log
from monitoring.reference import get_champion_reference


# ambil window dan threshold monitoring dari cli biar gampang didemo saat workshop
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="evaluate prediction log yang ground truth-nya sudah tersedia"
    )
    parser.add_argument(
        "--degradation-multiplier",
        type=float,
        default=1.25,
        help="retrain kalau recent MAE melewati reference MAE x multiplier",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=100,
        help="jumlah evaluation minimum sebelum boleh recommend retraining",
    )
    parser.add_argument(
        "--recent-limit",
        type=int,
        default=500,
        help="maksimum prediction terbaru yang dipakai buat recent metric",
    )

    return parser.parse_args()


# evaluate champion prediction lalu tulis artifact yang nanti dibaca prometheus dan airflow
def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]

    prediction_path = root / "data" / "monitoring" / "predictions.jsonl"
    evaluation_path = root / "data" / "monitoring" / "evaluations.parquet"
    summary_path = root / "data" / "monitoring" / "performance_summary.json"
    demand_dir = root / "data" / "processed" / "demand"

    # champion validation MAE jadi reference, bukan threshold angka random
    reference = get_champion_reference()
    records = load_prediction_log(prediction_path)

    evaluations = build_evaluation_table(
        prediction_records=records,
        demand_dir=demand_dir,
        model_version=str(reference["model_version"]),
    )
    summary = summarize_performance(
        evaluations=evaluations,
        reference_mae=float(reference["reference_mae"]),
        degradation_multiplier=args.degradation_multiplier,
        min_samples=args.min_samples,
        recent_limit=args.recent_limit,
    )
    summary.update(
        {
            "model_name": reference["model_name"],
            "model_version": reference["model_version"],
            "run_id": reference["run_id"],
        }
    )

    save_performance_artifacts(
        evaluations=evaluations,
        summary=summary,
        evaluation_path=evaluation_path,
        summary_path=summary_path,
    )

    print("\nmodel performance")
    print(f"model version: {summary['model_version']}")
    print(f"evaluation status: {summary['evaluation_status']}")
    print(f"evaluated at (UTC): {summary['evaluated_at']}")
    print(f"evaluated: {summary['evaluation_count']}")
    print(f"minimum samples: {summary['min_samples']}")
    print(f"reference MAE: {summary['reference_mae']:.3f}")

    if summary["recent_mae"] is None:
        print("recent MAE: belum ada ground truth yang bisa dievaluate")
    else:
        print(f"recent MAE: {summary['recent_mae']:.3f}")
        print(f"threshold MAE: {summary['threshold_mae']:.3f}")

    print(f"retrain recommended: {summary['retrain_recommended']}")
    print(f"latest replay target (NYC): {summary['latest_target_datetime']}")
    print(summary_path)


if __name__ == "__main__":
    main()
