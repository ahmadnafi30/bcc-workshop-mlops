from datetime import date
from pathlib import Path

import pandas as pd

from data_versioning.pipeline_files import (
    iter_csv_chunks,
    read_csv_dataset,
    write_csv_atomic,
)


# ambil trip untuk satu tanggal lalu release ke folder raw production
def release_daily_batch(
    target_date: date,
    source_path: Path,
    output_path: Path,
    force: bool = False,
) -> dict[str, int | str]:
    # kalau daily batch sudah pernah direlease kita cukup baca summary-nya
    if output_path.exists() and not force:
        existing = read_csv_dataset(
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
            f"replay source belum ada: {source_path}. jalanin scripts/bootstrap_data.py dulu."
        )

    # bikin window satu hari dari jam 00:00 sampai sebelum hari berikutnya
    day_start = pd.Timestamp(target_date)
    day_end = day_start + pd.Timedelta(days=1)

    # Monthly CSV is scanned in chunks; only this day's rows are held in memory.
    frames = []
    for trips in iter_csv_chunks(source_path, ["tpep_pickup_datetime", "PULocationID"]):
        selected = trips.loc[
            trips["tpep_pickup_datetime"].between(day_start, day_end, inclusive="left")
        ].copy()
        if not selected.empty:
            frames.append(selected)
    if not frames:
        raise ValueError(f"nggak ada trip buat tanggal {target_date.isoformat()}")
    daily = pd.concat(frames, ignore_index=True)

    # urutin row lalu simpan batch ke folder raw production
    daily = daily.sort_values("tpep_pickup_datetime").reset_index(drop=True)
    write_csv_atomic(daily, output_path)

    return {
        "date": target_date.isoformat(),
        "rows": len(daily),
        "zones": int(daily["PULocationID"].nunique()),
        "path": str(output_path),
        "status": "released",
    }


# validasi daily batch supaya step berikutnya nggak nerima data kosong atau salah tanggal
def validate_daily_batch(
    batch_path: Path,
    target_date: date,
) -> dict[str, int | str]:
    # baca dua kolom minimum yang memang dibutuhin pipeline setelah ingestion
    batch_path = Path(batch_path)

    if not batch_path.exists():
        raise FileNotFoundError(f"daily batch belum ada: {batch_path}")

    trips = read_csv_dataset(
        batch_path,
        columns=["tpep_pickup_datetime", "PULocationID"],
    )

    if trips.empty:
        raise ValueError(f"daily batch kosong: {batch_path}")

    # semua timestamp harus benar-benar berada pada tanggal replay yang diminta
    pickup_time = pd.to_datetime(
        trips["tpep_pickup_datetime"],
        errors="coerce",
    )

    if pickup_time.isna().any():
        raise ValueError("daily batch punya pickup timestamp yang invalid")

    actual_dates = set(pickup_time.dt.date.unique().tolist())
    if actual_dates != {target_date}:
        raise ValueError(f"daily batch punya tanggal di luar {target_date.isoformat()}")

    # zone id juga nggak boleh missing karena dipakai untuk aggregation
    if trips["PULocationID"].isna().any():
        raise ValueError("daily batch punya PULocationID yang kosong")

    return {
        "date": target_date.isoformat(),
        "rows": len(trips),
        "zones": int(trips["PULocationID"].nunique()),
        "path": str(batch_path),
        "status": "valid",
    }
