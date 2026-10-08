import json
import re
from pathlib import Path

import pandas as pd
import requests

from data_versioning.pipeline_files import (
    file_fingerprint,
    iter_csv_chunks,
    write_csv_chunks_atomic,
    write_json_atomic,
)
from ingestion.csv_source import convert_parquet_to_csv

TLC_TRIP_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
TLC_ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# cek format bulan dulu biar nama file dan url yang dibikin tetap konsisten
def validate_month(month: str) -> str:
    # pastiin input bulan punya format YYYY-MM yang valid sebelum dipakai ke mana-mana
    if not MONTH_PATTERN.fullmatch(month):
        raise ValueError(f"format bulan harus YYYY-MM, dapat: {month}")

    return month


# bikin url official yellow taxi parquet sesuai bulan yang diminta
def build_trip_url(month: str) -> str:
    # validasi bulan dulu lalu gabungin ke naming pattern official TLC
    validate_month(month)
    return f"{TLC_TRIP_BASE_URL}/yellow_tripdata_{month}.parquet"


# download file secara streaming dan skip kalau file lokalnya sudah ada
def download_file(url: str, destination: Path, force: bool = False) -> Path:
    # siapin path tujuan dan folder parent sebelum mulai download
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    # kalau file sudah ada kita pakai yang lokal aja, kecuali force dinyalain
    if destination.exists() and not force:
        return destination

    # download masuk ke file sementara dulu biar file final nggak setengah jadi kalau gagal
    temporary_path = destination.with_suffix(destination.suffix + ".part")

    try:
        # streaming dipakai supaya file parquet besar nggak langsung dimuat ke memory
        with requests.get(url, stream=True, timeout=(15, 180)) as response:
            response.raise_for_status()

            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        # setelah download sukses baru file sementara dipindah jadi file final
        temporary_path.replace(destination)

    except Exception:
        # bersihin file setengah jadi supaya run berikutnya mulai dari kondisi yang jelas
        temporary_path.unlink(missing_ok=True)
        raise

    return destination


# download official Parquet, lalu langsung konversi menjadi CSV untuk semua proses berikutnya
def download_monthly_trip_data(
    month: str,
    destination_dir: Path,
    force: bool = False,
) -> Path:
    # bikin nama file monthly parquet lalu pakai helper download yang sama
    validate_month(month)
    destination = Path(destination_dir) / f"yellow_tripdata_{month}.parquet"

    downloaded = download_file(build_trip_url(month), destination, force=force)
    converted = convert_parquet_to_csv(downloaded, force=force)
    print(f"monthly CSV {converted['status']}: {converted['rows']:,} rows -> {converted['path']}")
    return Path(converted["path"])


# ambil taxi zone lookup yang nanti dipakai buat filter pickup zone manhattan
def download_zone_lookup(destination: Path, force: bool = False) -> Path:
    # zone lookup cuma satu file, jadi tinggal download dari url metadata official TLC
    return download_file(TLC_ZONE_LOOKUP_URL, Path(destination), force=force)


# ambil daftar zone manhattan dan rapihin nama kolom yang kita butuhin
def load_manhattan_zones(zone_lookup_path: Path) -> pd.DataFrame:
    # baca lookup dan cek schema minimum sebelum dipakai buat filtering
    zones = pd.read_csv(zone_lookup_path)
    required_columns = {"LocationID", "Borough", "Zone"}
    missing_columns = required_columns.difference(zones.columns)

    if missing_columns:
        raise ValueError("taxi zone lookup kehilangan kolom: " + ", ".join(sorted(missing_columns)))

    # ambil zone yang borough-nya Manhattan dan simpan kolom yang memang kita pakai
    manhattan = zones.loc[
        zones["Borough"].astype(str).str.casefold().eq("manhattan"),
        ["LocationID", "Borough", "Zone"],
    ].copy()

    # samain tipe zone id biar join dan filtering nanti lebih ringan dan konsisten
    manhattan["LocationID"] = pd.to_numeric(
        manhattan["LocationID"],
        errors="raise",
    ).astype("int16")

    return manhattan.sort_values("LocationID").reset_index(drop=True)


# ringkas monthly CSV menjadi pickup Manhattan; Parquet hanya dibaca saat konversi download
def prepare_replay_month(
    source_path: Path,
    zone_lookup_path: Path,
    output_path: Path,
    month: str,
    force: bool = False,
) -> dict[str, int | str]:
    # validasi input dan normalisasi output path dulu
    validate_month(month)
    output_path = Path(output_path)

    if Path(source_path).suffix != ".csv" or output_path.suffix != ".csv":
        raise ValueError("replay preparation memakai CSV; jalankan bootstrap untuk konversi source")
    inputs = {
        "source_sha256": file_fingerprint(source_path),
        "zone_lookup_sha256": file_fingerprint(zone_lookup_path),
        "code_sha256": file_fingerprint(Path(__file__)),
        "month": month,
    }
    manifest_path = output_path.with_suffix(".metadata.json")
    if output_path.exists() and manifest_path.exists() and not force:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["inputs"] == inputs and manifest["output_sha256"] == file_fingerprint(
                output_path
            ):
                return {
                    "month": month,
                    "rows": manifest["rows"],
                    "zones": manifest["zones"],
                    "path": str(output_path),
                    "status": "skipped",
                }
        except (OSError, ValueError, KeyError, TypeError):
            pass

    manhattan_zones = load_manhattan_zones(zone_lookup_path)
    valid_zone_ids = set(manhattan_zones["LocationID"].tolist())
    month_start = pd.Timestamp(f"{month}-01")
    month_end = month_start + pd.offsets.MonthBegin(1)
    observed_zones = set()

    def filtered_chunks():
        for trips in iter_csv_chunks(source_path, ["tpep_pickup_datetime", "PULocationID"]):
            trips["PULocationID"] = pd.to_numeric(trips["PULocationID"], errors="coerce")
            valid_rows = trips["tpep_pickup_datetime"].between(
                month_start, month_end, inclusive="left"
            ) & trips["PULocationID"].isin(valid_zone_ids)
            replay = trips.loc[valid_rows, ["tpep_pickup_datetime", "PULocationID"]].dropna().copy()
            replay["PULocationID"] = replay["PULocationID"].astype("int16")
            observed_zones.update(replay["PULocationID"].unique().tolist())
            yield replay

    rows = write_csv_chunks_atomic(filtered_chunks(), output_path)
    write_json_atomic(
        {
            "inputs": inputs,
            "output_sha256": file_fingerprint(output_path),
            "rows": rows,
            "zones": len(observed_zones),
        },
        manifest_path,
    )
    return {
        "month": month,
        "rows": rows,
        "zones": len(observed_zones),
        "path": str(output_path),
        "status": "prepared",
    }
