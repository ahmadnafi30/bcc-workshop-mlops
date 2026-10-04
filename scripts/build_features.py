import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from features.build_features import build_model_features


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
        "--force",
        action="store_true",
        help="timpa feature parquet kalau output sudah ada",
    )

    return parser.parse_args()


# load seluruh daily demand dalam range dan kasih error jelas kalau ada hari yang bolong
def load_demand_range(
    demand_dir: Path,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    # kumpulin file per hari supaya urutan history-nya explicit dan reproducible
    frames = []
    missing_dates = []

    for timestamp in pd.date_range(start_date, end_date, freq="D"):
        target_date = timestamp.date()
        path = demand_dir / f"{target_date.isoformat()}.parquet"

        if not path.exists():
            missing_dates.append(target_date.isoformat())
            continue

        frames.append(pd.read_parquet(path))

    # feature engineering sebaiknya gagal kalau history bolong daripada diam-diam bikin lag salah
    if missing_dates:
        preview = ", ".join(missing_dates[:5])
        suffix = "..." if len(missing_dates) > 5 else ""
        raise FileNotFoundError(
            f"processed demand belum lengkap: {preview}{suffix}. "
            "jalanin scripts/prepare_historical_demand.py dulu."
        )

    if not frames:
        raise ValueError("nggak ada processed demand yang bisa digabung")

    return pd.concat(frames, ignore_index=True)


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
    output_path = root / "data" / "features" / "taxi_demand_features.parquet"

    # skip output existing supaya run manual tetap idempotent
    if output_path.exists() and not args.force:
        print(f"feature dataset sudah ada, skip: {output_path}")
        return

    # gabung demand history lalu bikin lag, rolling, dan calendar feature
    demand = load_demand_range(
        demand_dir=demand_dir,
        start_date=start_date,
        end_date=end_date,
    )
    features = build_model_features(demand)

    # simpan satu parquet model-ready yang nanti dipakai training dan MLflow
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)

    print(
        f"features selesai -> {len(features):,} rows, "
        f"{features['zone_id'].nunique()} zones"
    )
    print(
        f"target range: {features['timestamp'].min()} "
        f"sampai {features['timestamp'].max()}"
    )
    print(output_path)


if __name__ == "__main__":
    main()
