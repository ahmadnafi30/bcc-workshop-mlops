import argparse
from datetime import date
from pathlib import Path

from ingestion.replay import release_daily_batch


# ambil tanggal replay dari cli biar satu run cuma ngelepas satu daily batch
def parse_args() -> argparse.Namespace:
    # parser ini cukup nerima tanggal production dan opsi force
    parser = argparse.ArgumentParser(
        description="release satu hari historical trip sebagai production batch"
    )

    parser.add_argument(
        "--date",
        required=True,
        help="tanggal yang mau direplay, format YYYY-MM-DD",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="timpa daily batch kalau file output sudah ada",
    )

    return parser.parse_args()


# jalanin historical replay untuk tanggal yang dipilih dari command line
def main() -> None:
    # parse tanggal dan cari monthly replay source yang sesuai
    args = parse_args()
    target_date = date.fromisoformat(args.date)
    root = Path(__file__).resolve().parents[1]
    month = target_date.strftime("%Y-%m")

    source_path = (
        root
        / "data"
        / "source"
        / "replay"
        / f"yellow_tripdata_{month}.parquet"
    )

    # output raw sengaja satu file per hari biar gampang dipetakan ke Airflow
    output_path = (
        root
        / "data"
        / "raw"
        / "trips"
        / f"{target_date.isoformat()}.parquet"
    )

    summary = release_daily_batch(
        target_date=target_date,
        source_path=source_path,
        output_path=output_path,
        force=args.force,
    )

    print(
        f"{summary['date']} -> "
        f"{summary['rows']:,} trips, "
        f"{summary['zones']} zones, "
        f"{summary['status']}"
    )
    print(summary["path"])


if __name__ == "__main__":
    main()
