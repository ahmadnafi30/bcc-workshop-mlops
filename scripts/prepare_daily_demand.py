import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from data_versioning.pipeline_files import read_csv_dataset, write_csv_atomic
from preprocessing.aggregate_demand import aggregate_hourly_demand


# ambil tanggal batch yang mau diubah dari raw trip jadi hourly demand
def parse_args() -> argparse.Namespace:
    # parser cukup nerima tanggal batch dan opsi overwrite
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


# baca daily batch, aggregate demand per zone per jam, lalu simpan hasilnya
def main() -> None:
    # ambil tanggal dan siapin seluruh path input-output dari root repository
    args = parse_args()
    target_date = date.fromisoformat(args.date)
    root = Path(__file__).resolve().parents[1]

    trip_path = root / "data" / "raw" / "trips" / f"{target_date.isoformat()}.csv"
    zone_lookup_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"
    output_path = root / "data" / "processed" / "demand" / f"{target_date.isoformat()}.csv"

    # processed file nggak perlu dibuat ulang kecuali force memang diminta
    if output_path.exists() and not args.force:
        print(f"processed demand sudah ada, skip: {output_path}")
        return

    # kasih error yang jelas kalau urutan manual pipeline-nya belum lengkap
    if not trip_path.exists():
        raise FileNotFoundError(
            f"daily batch belum ada: {trip_path}. jalanin simulate_daily_data.py dulu."
        )

    if not zone_lookup_path.exists():
        raise FileNotFoundError(
            f"taxi zone lookup belum ada: {zone_lookup_path}. jalanin bootstrap_data.py dulu."
        )

    # load raw batch dan metadata lalu ubah trip-level data jadi hourly demand
    trips = read_csv_dataset(trip_path)
    zone_lookup = pd.read_csv(zone_lookup_path)
    demand = aggregate_hourly_demand(
        trips=trips,
        zone_lookup=zone_lookup,
        target_date=target_date,
    )

    # simpan hasil processed sebagai CSV supaya step berikutnya tinggal baca
    write_csv_atomic(demand, output_path)

    # kasih summary sederhana buat quick sanity check dari terminal
    print(
        f"{target_date.isoformat()} -> "
        f"{len(demand):,} zone-hour rows, "
        f"{demand['trip_count'].sum():,} pickups"
    )
    print(output_path)


if __name__ == "__main__":
    main()
