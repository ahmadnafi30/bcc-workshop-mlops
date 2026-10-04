import argparse
from datetime import date
from pathlib import Path

import pandas as pd


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


# ambil trip untuk satu tanggal lalu release ke folder raw production
def release_daily_batch(
    target_date: date,
    source_path: Path,
    output_path: Path,
    force: bool = False,
) -> dict[str, int | str]:
    # kalau daily batch sudah pernah direlease kita cukup baca summary-nya
    if output_path.exists() and not force:
        existing = pd.read_parquet(
            output_path,
            columns=["tpep_pickup_datetime", "PULocationID"],
        )

        return {
            "date": target_date.isoformat(),
            "rows": len(existing),
            "zones": int(existing["PULocationID"].nunique()),
            "path": str(output_path),
            "status": "skipped",
        }

    # replay source harus disiapin bootstrap dulu sebelum satu hari bisa direlease
    if not source_path.exists():
        raise FileNotFoundError(
            f"replay source belum ada: {source_path}. "
            "jalanin scripts/bootstrap_data.py dulu."
        )

    # baca monthly replay source lalu samain pickup time ke tipe datetime
    trips = pd.read_parquet(
        source_path,
        columns=["tpep_pickup_datetime", "PULocationID"],
    )
    trips["tpep_pickup_datetime"] = pd.to_datetime(
        trips["tpep_pickup_datetime"],
        errors="coerce",
    )

    # bikin window satu hari dari jam 00:00 sampai sebelum hari berikutnya
    day_start = pd.Timestamp(target_date)
    day_end = day_start + pd.Timedelta(days=1)

    # ambil cuma trip yang seolah-olah baru available pada tanggal replay ini
    daily = trips.loc[
        trips["tpep_pickup_datetime"].between(
            day_start,
            day_end,
            inclusive="left",
        )
    ].copy()

    # empty batch biasanya berarti tanggalnya salah atau source month-nya nggak sesuai
    if daily.empty:
        raise ValueError(f"nggak ada trip buat tanggal {target_date.isoformat()}")

    # urutin row lalu simpan batch ke folder raw production
    daily = daily.sort_values("tpep_pickup_datetime").reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(output_path, index=False)

    return {
        "date": target_date.isoformat(),
        "rows": len(daily),
        "zones": int(daily["PULocationID"].nunique()),
        "path": str(output_path),
        "status": "released",
    }


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

    # output raw sengaja satu file per hari biar gampang dipetakan ke Airflow logical date
    output_path = (
        root
        / "data"
        / "raw"
        / "trips"
        / f"{target_date.isoformat()}.parquet"
    )

    # release batch lalu tampilkan summary-nya ke terminal
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
