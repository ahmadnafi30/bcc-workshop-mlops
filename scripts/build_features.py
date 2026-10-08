import argparse
from datetime import date
from pathlib import Path

from features.dataset import build_feature_dataset


# ambil date range hourly demand yang mau digabung jadi model-ready feature dataset
def parse_args() -> argparse.Namespace:
    # default range sama dengan history initial training dan validation
    parser = argparse.ArgumentParser(
        description="gabung hourly demand lalu bikin taxi demand features"
    )
    parser.add_argument(
        "--start-date",
        default="2025-01-01",
        help="tanggal awal demand history, format YYYY-MM-DD",
    )
    parser.add_argument(
        "--end-date",
        default="2025-01-26",
        help="tanggal akhir demand history, format YYYY-MM-DD",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/features/taxi_demand_features.parquet"),
        help="lokasi output; DVC memakai file training terpisah dari replay",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="rebuild walaupun cache input/output masih sesuai",
    )

    return parser.parse_args()


# bangun model-ready feature dataset dari hourly demand yang sudah disiapin
def main() -> None:
    # parse range dan siapin lokasi input-output dari root repository
    args = parse_args()
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)

    if end_date < start_date:
        raise ValueError("end-date harus sama atau setelah start-date")

    root = Path(__file__).resolve().parents[1]
    demand_dir = root / "data" / "processed" / "demand"
    output_path = root / args.output_path

    summary = build_feature_dataset(
        demand_dir=demand_dir,
        output_path=output_path,
        start_date=start_date,
        end_date=end_date,
        use_cache=not args.force,
    )

    print(f"features {summary['status']} -> {summary['rows']:,} rows, {summary['zones']} zones")
    print(f"target range: {summary['start_timestamp']} sampai {summary['end_timestamp']}")
    print(summary["path"])


if __name__ == "__main__":
    main()
