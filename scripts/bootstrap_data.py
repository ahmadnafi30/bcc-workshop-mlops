import argparse
from pathlib import Path

from ingestion.taxi import (
    download_monthly_trip_data,
    download_zone_lookup,
    prepare_replay_month,
)

DEFAULT_MONTHS = ["2025-01", "2025-02", "2025-03"]


# ambil opsi cli biar bulan dan force mode gampang diganti saat workshop
def parse_args() -> argparse.Namespace:
    # siapin argument parser buat milih month dan force mode dari terminal
    parser = argparse.ArgumentParser(
        description="download dan siapin NYC TLC data buat historical replay"
    )

    # default-nya pakai tiga bulan, tapi peserta tetap bisa pilih month tertentu
    parser.add_argument(
        "--months",
        nargs="+",
        default=DEFAULT_MONTHS,
        help="bulan yang mau disiapin, format YYYY-MM",
    )

    # force dipakai kalau kita memang mau overwrite hasil bootstrap sebelumnya
    parser.add_argument(
        "--force",
        action="store_true",
        help="download dan prepare ulang walaupun file lokal sudah ada",
    )

    return parser.parse_args()


# jalanin bootstrap dari download raw monthly file sampai replay source siap
def main() -> None:
    # ambil argumen dan tentuin semua path relatif dari root repository
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    source_dir = root / "data" / "source" / "tlc"
    replay_dir = root / "data" / "source" / "replay"
    metadata_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"

    # zone lookup cukup didownload sekali karena dipakai untuk semua month
    print("downloading taxi zone lookup...")
    download_zone_lookup(metadata_path, force=args.force)

    summaries = []

    # tiap month didownload lalu diringkas jadi replay source khusus pickup Manhattan
    for month in args.months:
        print(f"\npreparing {month}...")

        monthly_path = download_monthly_trip_data(
            month,
            source_dir,
            force=args.force,
        )

        replay_path = replay_dir / f"yellow_tripdata_{month}.csv"

        summary = prepare_replay_month(
            source_path=monthly_path,
            zone_lookup_path=metadata_path,
            output_path=replay_path,
            month=month,
            force=args.force,
        )
        summaries.append(summary)

    # tampilkan summary singkat supaya kita langsung tahu hasil bootstrap-nya masuk akal
    print("\nbootstrap selesai")
    for summary in summaries:
        print(
            f"- {summary['month']}: "
            f"{summary['rows']:,} trips, "
            f"{summary['zones']} zones, "
            f"{summary['status']}"
        )


if __name__ == "__main__":
    main()
