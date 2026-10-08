import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from data_versioning.pipeline_files import read_csv_dataset, write_csv_atomic
from preprocessing.aggregate_demand import aggregate_hourly_demand


# ambil date range yang mau disiapin sebagai history awal sebelum production replay
def parse_args() -> argparse.Namespace:
    # default range mencakup warm-up, training, dan validation awal
    parser = argparse.ArgumentParser(
        description="siapin hourly demand historical buat initial model training"
    )
    parser.add_argument(
        "--start-date",
        default="2025-01-01",
        help="tanggal awal history, format YYYY-MM-DD",
    )
    parser.add_argument(
        "--end-date",
        default="2025-01-26",
        help="tanggal akhir history, format YYYY-MM-DD",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="timpa processed daily demand yang sudah ada",
    )

    return parser.parse_args()


# load monthly replay source cuma saat month berubah biar file besar nggak dibaca berulang
def load_month_source(root: Path, month: str) -> pd.DataFrame:
    # initial history tetap diambil dari replay source hasil bootstrap
    source_path = root / "data" / "source" / "replay" / f"yellow_tripdata_{month}.csv"

    if not source_path.exists():
        raise FileNotFoundError(
            f"replay source belum ada: {source_path}. jalanin scripts/bootstrap_data.py dulu."
        )

    return read_csv_dataset(
        source_path,
        columns=["tpep_pickup_datetime", "PULocationID"],
    )


# siapin hourly demand untuk seluruh history awal tanpa perlu release raw batch satu-satu
def main() -> None:
    # parse range lalu cek end date nggak lebih kecil dari start date
    args = parse_args()
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)

    if end_date < start_date:
        raise ValueError("end-date harus sama atau setelah start-date")

    # load zone lookup sekali karena metadata ini dipakai untuk semua hari
    root = Path(__file__).resolve().parents[1]
    zone_lookup_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"

    if not zone_lookup_path.exists():
        raise FileNotFoundError(
            f"taxi zone lookup belum ada: {zone_lookup_path}. "
            "jalanin scripts/bootstrap_data.py dulu."
        )

    zone_lookup = pd.read_csv(zone_lookup_path)
    current_month = None
    month_trips = None
    prepared = 0
    skipped = 0

    # jalan dari start sampai end date dan reuse monthly dataframe selama month-nya sama
    for timestamp in pd.date_range(start_date, end_date, freq="D"):
        target_date = timestamp.date()
        month = timestamp.strftime("%Y-%m")

        if month != current_month:
            month_trips = load_month_source(root, month)
            current_month = month

        output_path = root / "data" / "processed" / "demand" / f"{target_date.isoformat()}.csv"

        if output_path.exists() and not args.force:
            skipped += 1
            continue

        # aggregate satu hari jadi complete Manhattan zone-hour grid
        demand = aggregate_hourly_demand(
            trips=month_trips,
            zone_lookup=zone_lookup,
            target_date=target_date,
        )

        write_csv_atomic(demand, output_path)
        prepared += 1

    # summary ini cukup buat quick check sebelum lanjut feature engineering
    print(
        f"history {start_date} sampai {end_date} selesai -> {prepared} prepared, {skipped} skipped"
    )


if __name__ == "__main__":
    main()
