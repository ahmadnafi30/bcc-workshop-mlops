from pathlib import Path
import re

import pandas as pd
import requests

TLC_TRIP_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
TLC_ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validate_month(month: str) -> str:
    """cek format bulan dulu biar nama file dan url yang dibikin tetap konsisten."""
    if not MONTH_PATTERN.fullmatch(month):
        raise ValueError(f"format bulan harus YYYY-MM, dapat: {month}")
    return month


def build_trip_url(month: str) -> str:
    """bikin url official yellow taxi parquet sesuai bulan yang diminta."""
    validate_month(month)
    return f"{TLC_TRIP_BASE_URL}/yellow_tripdata_{month}.parquet"


def download_file(url: str, destination: Path, force: bool = False) -> Path:
    """download file secara streaming dan skip kalau file lokalnya sudah ada."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not force:
        return destination

    temporary_path = destination.with_suffix(destination.suffix + ".part")

    try:
        with requests.get(url, stream=True, timeout=(15, 180)) as response:
            response.raise_for_status()
            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return destination


def download_monthly_trip_data(
    month: str,
    destination_dir: Path,
    force: bool = False,
) -> Path:
    """ambil yellow taxi parquet untuk satu bulan dan simpan sebagai source data."""
    validate_month(month)
    destination = Path(destination_dir) / f"yellow_tripdata_{month}.parquet"
    return download_file(build_trip_url(month), destination, force=force)


def download_zone_lookup(destination: Path, force: bool = False) -> Path:
    """ambil taxi zone lookup yang nanti dipakai buat filter pickup zone manhattan."""
    return download_file(TLC_ZONE_LOOKUP_URL, Path(destination), force=force)


def load_manhattan_zones(zone_lookup_path: Path) -> pd.DataFrame:
    """ambil daftar zone manhattan dan rapihin nama kolom yang kita butuhin."""
    zones = pd.read_csv(zone_lookup_path)
    required_columns = {"LocationID", "Borough", "Zone"}
    missing_columns = required_columns.difference(zones.columns)

    if missing_columns:
        raise ValueError(
            "taxi zone lookup kehilangan kolom: "
            + ", ".join(sorted(missing_columns))
        )

    manhattan = zones.loc[
        zones["Borough"].astype(str).str.casefold().eq("manhattan"),
        ["LocationID", "Borough", "Zone"],
    ].copy()

    manhattan["LocationID"] = pd.to_numeric(
        manhattan["LocationID"], errors="raise"
    ).astype("int16")

    return manhattan.sort_values("LocationID").reset_index(drop=True)


def prepare_replay_month(
    source_path: Path,
    zone_lookup_path: Path,
    output_path: Path,
    month: str,
    force: bool = False,
) -> dict[str, int | str]:
    """ringkas monthly parquet jadi pickup manhattan yang enak dipakai buat replay."""
    validate_month(month)
    output_path = Path(output_path)

    if output_path.exists() and not force:
        existing = pd.read_parquet(
            output_path,
            columns=["tpep_pickup_datetime", "PULocationID"],
        )
        return {
            "month": month,
            "rows": len(existing),
            "zones": int(existing["PULocationID"].nunique()),
            "path": str(output_path),
            "status": "skipped",
        }

    trips = pd.read_parquet(
        source_path,
        columns=["tpep_pickup_datetime", "PULocationID"],
    )
    trips["tpep_pickup_datetime"] = pd.to_datetime(
        trips["tpep_pickup_datetime"],
        errors="coerce",
    )
    trips["PULocationID"] = pd.to_numeric(
        trips["PULocationID"],
        errors="coerce",
    )

    manhattan_zones = load_manhattan_zones(zone_lookup_path)
    valid_zone_ids = set(manhattan_zones["LocationID"].tolist())

    month_start = pd.Timestamp(f"{month}-01")
    month_end = month_start + pd.offsets.MonthBegin(1)

    valid_rows = (
        trips["tpep_pickup_datetime"].between(
            month_start,
            month_end,
            inclusive="left",
        )
        & trips["PULocationID"].isin(valid_zone_ids)
    )

    replay = trips.loc[
        valid_rows,
        ["tpep_pickup_datetime", "PULocationID"],
    ].dropna()

    replay["PULocationID"] = replay["PULocationID"].astype("int16")
    replay = replay.sort_values("tpep_pickup_datetime").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    replay.to_parquet(output_path, index=False)

    return {
        "month": month,
        "rows": len(replay),
        "zones": int(replay["PULocationID"].nunique()),
        "path": str(output_path),
        "status": "prepared",
    }
