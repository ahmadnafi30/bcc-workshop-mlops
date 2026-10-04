from datetime import date
from pathlib import Path

import pandas as pd

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
    source_path = (
        Path(project_root)
        / "data"
        / "source"
        / "replay"
        / f"yellow_tripdata_{month}.parquet"
    )
    output_path = (
        Path(project_root)
        / "data"
        / "raw"
        / "trips"
        / f"{replay_date}.parquet"
    )

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
    batch_path = (
        Path(project_root)
        / "data"
        / "raw"
        / "trips"
        / f"{replay_date}.parquet"
    )

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
    trip_path = root / "data" / "raw" / "trips" / f"{replay_date}.parquet"
    zone_lookup_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"
    output_path = (
        root
        / "data"
        / "processed"
        / "demand"
        / f"{replay_date}.parquet"
    )

    if not trip_path.exists():
        raise FileNotFoundError(f"daily batch belum ada: {trip_path}")

    if not zone_lookup_path.exists():
        raise FileNotFoundError(f"taxi zone lookup belum ada: {zone_lookup_path}")

    # aggregation reuse business logic yang sama dengan manual pipeline
    trips = pd.read_parquet(trip_path)
    zone_lookup = pd.read_csv(zone_lookup_path)
    demand = aggregate_hourly_demand(
        trips=trips,
        zone_lookup=zone_lookup,
        target_date=target_date,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    demand.to_parquet(output_path, index=False)

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
    output_path = root / "data" / "features" / "taxi_demand_features.parquet"

    return build_feature_dataset(
        demand_dir=demand_dir,
        output_path=output_path,
        start_date=HISTORY_START_DATE,
        end_date=target_date,
    )
