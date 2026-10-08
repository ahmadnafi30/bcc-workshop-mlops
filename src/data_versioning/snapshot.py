from hashlib import sha256
from pathlib import Path

import pandas as pd

from data_versioning.pipeline_files import read_csv_dataset


# bikin nama snapshot yang konsisten dari cutoff date
def build_snapshot_name(cutoff_date: str) -> str:
    # format nama file dibuat predictable supaya gampang dipakai DVC dan training
    return f"taxi_demand_{cutoff_date}.csv"


# bikin snapshot training dari feature dataset sampai cutoff date tertentu
def create_training_snapshot(
    features: pd.DataFrame,
    cutoff_date: str,
) -> pd.DataFrame:
    # timestamp dirapihin dulu supaya filtering berdasarkan waktu tetap konsisten
    snapshot = features.copy()
    snapshot["timestamp"] = pd.to_datetime(
        snapshot["timestamp"],
        errors="raise",
    )

    # cutoff bersifat inclusive sampai akhir hari yang dipilih
    cutoff_end = pd.Timestamp(cutoff_date) + pd.Timedelta(days=1)
    snapshot = snapshot.loc[snapshot["timestamp"] < cutoff_end].copy()

    if snapshot.empty:
        raise ValueError(f"snapshot kosong untuk cutoff date {cutoff_date}")

    # urutin row supaya snapshot gampang dibandingin dan reproducible
    return snapshot.sort_values(["timestamp", "zone_id"]).reset_index(drop=True)


# hitung fingerprint file snapshot supaya MLflow bisa nyatet dataset version yang dipakai
def calculate_file_sha256(path: Path) -> str:
    # file dibaca per chunk supaya fingerprint tetap aman untuk file yang lumayan besar
    digest = sha256()

    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


# ambil metadata minimum snapshot yang berguna buat experiment tracking
def describe_snapshot(path: Path) -> dict[str, str | int]:
    # metadata diambil dari file final yang benar-benar dipakai training
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"training snapshot belum ada: {path}")

    snapshot = read_csv_dataset(
        path,
        columns=["timestamp", "zone_id"],
    )
    snapshot["timestamp"] = pd.to_datetime(
        snapshot["timestamp"],
        errors="raise",
    )

    return {
        "name": path.name,
        "sha256": calculate_file_sha256(path),
        "rows": len(snapshot),
        "zones": int(snapshot["zone_id"].nunique()),
        "start_timestamp": snapshot["timestamp"].min().isoformat(),
        "end_timestamp": snapshot["timestamp"].max().isoformat(),
    }
