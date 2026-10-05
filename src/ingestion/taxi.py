import re
from pathlib import Path

import pandas as pd
import requests

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


# ambil yellow taxi parquet untuk satu bulan dan simpan sebagai source data
def download_monthly_trip_data(
    month: str,
    destination_dir: Path,
    force: bool = False,
) -> Path:
    # bikin nama file monthly parquet lalu pakai helper download yang sama
    validate_month(month)
    destination = Path(destination_dir) / f"yellow_tripdata_{month}.parquet"

    return download_file(build_trip_url(month), destination, force=force)


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
        raise ValueError(
            "taxi zone lookup kehilangan kolom: "
            + ", ".join(sorted(missing_columns))
        )

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


# ringkas monthly parquet jadi pickup manhattan yang enak dipakai buat replay
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

    # kalau replay source sudah pernah dibuat kita cukup baca summary-nya
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

    # baca cuma dua kolom yang kita butuhin biar prosesnya lebih hemat memory
    trips = pd.read_parquet(
        source_path,
        columns=["tpep_pickup_datetime", "PULocationID"],
    )

    # rapihin tipe data karena source parquet tetap perlu kita anggap sebagai external input
    trips["tpep_pickup_datetime"] = pd.to_datetime(
        trips["tpep_pickup_datetime"],
        errors="coerce",
    )
    trips["PULocationID"] = pd.to_numeric(
        trips["PULocationID"],
        errors="coerce",
    )

    # ambil daftar zone yang valid supaya replay source cuma berisi pickup Manhattan
    manhattan_zones = load_manhattan_zones(zone_lookup_path)
    valid_zone_ids = set(manhattan_zones["LocationID"].tolist())

    # bikin batas awal dan akhir bulan buat buang timestamp nyasar di luar file month-nya
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

    # simpan cuma row valid dan dua kolom yang nanti dibutuhin historical replay
    replay = trips.loc[
        valid_rows,
        ["tpep_pickup_datetime", "PULocationID"],
    ].dropna()

    # rapihin tipe dan urutan waktu supaya file replay lebih predictable
    replay["PULocationID"] = replay["PULocationID"].astype("int16")
    replay = replay.sort_values("tpep_pickup_datetime").reset_index(drop=True)

    # tulis compact replay source ke parquet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    replay.to_parquet(output_path, index=False)

    return {
        "month": month,
        "rows": len(replay),
        "zones": int(replay["PULocationID"].nunique()),
        "path": str(output_path),
        "status": "prepared",
    }
