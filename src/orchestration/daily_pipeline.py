from datetime import date
from pathlib import Path

import pandas as pd

from data_versioning.pipeline_files import read_csv_dataset, write_csv_atomic
from features.dataset import build_feature_dataset
from ingestion.replay import (
    release_daily_batch,
    validate_daily_batch,
)
from preprocessing.aggregate_demand import aggregate_hourly_demand

HISTORY_START_DATE = date(2025, 1, 1)


# release satu tanggal dari monthly replay source ke folder raw production
def release_replay_batch(
    project_root: Path,
    replay_date: str,
) -> dict[str, int | str]:
    # path source dipilih berdasarkan month dari replay date
    target_date = date.fromisoformat(replay_date)
    month = target_date.strftime("%Y-%m")
    source_path = Path(project_root) / "data" / "source" / "replay" / f"yellow_tripdata_{month}.csv"
    output_path = Path(project_root) / "data" / "raw" / "trips" / f"{replay_date}.csv"

    return release_daily_batch(
        target_date=target_date,
        source_path=source_path,
        output_path=output_path,
        force=False,
    )


# validasi raw batch sebelum data masuk ke aggregation step
def validate_replay_batch(
    project_root: Path,
    replay_date: str,
) -> dict[str, int | str]:
    # validation baca file yang baru direlease dan cek tanggal serta schema minimum
    target_date = date.fromisoformat(replay_date)
    batch_path = Path(project_root) / "data" / "raw" / "trips" / f"{replay_date}.csv"

    return validate_daily_batch(
        batch_path=batch_path,
        target_date=target_date,
    )


# ubah raw daily trip jadi complete hourly demand per Manhattan zone
def prepare_replay_demand(
    project_root: Path,
    replay_date: str,
) -> dict[str, int | str]:
    # daily batch dan zone lookup jadi dua input utama aggregation
    root = Path(project_root)
    target_date = date.fromisoformat(replay_date)
    trip_path = root / "data" / "raw" / "trips" / f"{replay_date}.csv"
    zone_lookup_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"
    output_path = root / "data" / "processed" / "demand" / f"{replay_date}.csv"

    if not trip_path.exists():
        raise FileNotFoundError(f"daily batch belum ada: {trip_path}")

    if not zone_lookup_path.exists():
        raise FileNotFoundError(f"taxi zone lookup belum ada: {zone_lookup_path}")

    # aggregation reuse business logic yang sama dengan manual pipeline
    trips = read_csv_dataset(trip_path, columns=["tpep_pickup_datetime", "PULocationID"])
    zone_lookup = pd.read_csv(zone_lookup_path)
    demand = aggregate_hourly_demand(
        trips=trips,
        zone_lookup=zone_lookup,
        target_date=target_date,
    )

    write_csv_atomic(demand, output_path)

    return {
        "date": replay_date,
        "rows": len(demand),
        "zones": int(demand["zone_id"].nunique()),
        "pickups": int(demand["trip_count"].sum()),
        "path": str(output_path),
    }


# rebuild feature dataset dari history awal sampai replay date terbaru
def rebuild_replay_features(
    project_root: Path,
    replay_date: str,
) -> dict[str, int | str]:
    # full history dibaca ulang supaya lag dan rolling tetap punya context yang lengkap
    root = Path(project_root)
    target_date = date.fromisoformat(replay_date)
    demand_dir = root / "data" / "processed" / "demand"
    output_path = root / "data" / "features" / "taxi_demand_features.csv"

    # Rerunning an older batch must not remove newer hours from serving features.
    available_dates = [date.fromisoformat(path.stem) for path in demand_dir.glob("*.csv")]
    target_date = max([target_date, *available_dates])

    return build_feature_dataset(
        demand_dir=demand_dir,
        output_path=output_path,
        start_date=HISTORY_START_DATE,
        end_date=target_date,
    )
