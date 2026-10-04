import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from preprocessing.aggregate_demand import aggregate_hourly_demand


def parse_args() -> argparse.Namespace:
    """ambil tanggal batch yang mau diubah dari raw trip jadi hourly demand."""
    parser = argparse.ArgumentParser(
        description="aggregate satu daily trip batch jadi hourly taxi demand"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="tanggal batch, format YYYY-MM-DD",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="timpa processed file kalau output sudah ada",
    )
    return parser.parse_args()


def main() -> None:
    """baca daily batch, aggregate demand per zone per jam, lalu simpan hasilnya."""
    args = parse_args()
    target_date = date.fromisoformat(args.date)
    root = Path(__file__).resolve().parents[1]

    trip_path = (
        root
        / "data"
        / "raw"
        / "trips"
        / f"{target_date.isoformat()}.parquet"
    )
    zone_lookup_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"
    output_path = (
        root
        / "data"
        / "processed"
        / "demand"
        / f"{target_date.isoformat()}.parquet"
    )

    if output_path.exists() and not args.force:
        print(f"processed demand sudah ada, skip: {output_path}")
        return

    if not trip_path.exists():
        raise FileNotFoundError(
            f"daily batch belum ada: {trip_path}. "
            "jalanin simulate_daily_data.py dulu."
        )

    if not zone_lookup_path.exists():
        raise FileNotFoundError(
            f"taxi zone lookup belum ada: {zone_lookup_path}. "
            "jalanin bootstrap_data.py dulu."
        )

    trips = pd.read_parquet(trip_path)
    zone_lookup = pd.read_csv(zone_lookup_path)
    demand = aggregate_hourly_demand(
        trips=trips,
        zone_lookup=zone_lookup,
        target_date=target_date,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    demand.to_parquet(output_path, index=False)

    print(
        f"{target_date.isoformat()} -> "
        f"{len(demand):,} zone-hour rows, "
        f"{demand['trip_count'].sum():,} pickups"
    )
    print(output_path)


if __name__ == "__main__":
    main()
