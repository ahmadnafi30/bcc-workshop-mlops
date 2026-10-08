import json
import logging
from datetime import date
from pathlib import Path

import pandas as pd

from data_versioning.pipeline_files import (
    file_fingerprint,
    read_csv_dataset,
    write_csv_atomic,
    write_json_atomic,
)
from features.build_features import build_model_features

LOGGER = logging.getLogger(__name__)


# load seluruh daily demand dalam range dan gagal kalau ada tanggal yang bolong
def load_demand_range(
    demand_dir: Path,
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    # file dibaca per tanggal supaya missing batch gampang dideteksi
    frames = []
    missing_dates = []

    for timestamp in pd.date_range(start_date, end_date, freq="D"):
        target_date = timestamp.date()
        path = Path(demand_dir) / f"{target_date.isoformat()}.csv"

        if not path.exists():
            missing_dates.append(target_date.isoformat())
            continue

        frames.append(read_csv_dataset(path))

    # history bolong bisa bikin lag salah, jadi lebih aman fail daripada lanjut diam-diam
    if missing_dates:
        preview = ", ".join(missing_dates[:5])
        suffix = "..." if len(missing_dates) > 5 else ""
        raise FileNotFoundError(f"processed demand belum lengkap: {preview}{suffix}")

    if not frames:
        raise ValueError("nggak ada processed demand yang bisa digabung")

    return pd.concat(frames, ignore_index=True)


# gabung processed demand lalu tulis ulang model-ready feature dataset
def build_feature_dataset(
    demand_dir: Path,
    output_path: Path,
    start_date: date,
    end_date: date,
    use_cache: bool = True,
) -> dict[str, int | str]:
    if end_date < start_date:
        raise ValueError("end_date harus sama atau setelah start_date")
    output_path = Path(output_path)
    manifest_path = output_path.with_suffix(".metadata.json")
    # Check content, range, and code. File existence alone is not freshness.
    fingerprint = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "demand": {
            timestamp.date().isoformat(): file_fingerprint(
                Path(demand_dir) / f"{timestamp.date().isoformat()}.csv"
            )
            for timestamp in pd.date_range(start_date, end_date, freq="D")
        },
        "code": {
            path.name: file_fingerprint(path)
            for path in [
                Path(__file__),
                Path(__file__).with_name("build_features.py"),
                Path(__file__).resolve().parents[1] / "data_versioning/pipeline_files.py",
            ]
        },
        "pandas_version": pd.__version__,
    }
    if use_cache and output_path.exists() and manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["inputs"] == fingerprint and manifest["output_sha256"] == file_fingerprint(
                output_path
            ):
                summary = manifest["summary"]
                if {
                    "rows",
                    "zones",
                    "start_timestamp",
                    "end_timestamp",
                } <= summary.keys():
                    LOGGER.info(
                        "Feature cache HIT: input, range, code, output tidak berubah: %s",
                        output_path,
                    )
                    return {**summary, "path": str(output_path), "status": "cached"}
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            LOGGER.info("Feature manifest tidak valid; rebuild %s", output_path)
    LOGGER.info("Feature cache MISS: membangun features %s sampai %s", start_date, end_date)
    # feature selalu dibangun dari full history sampai end date supaya lag tetap konsisten
    demand = load_demand_range(
        demand_dir=demand_dir,
        start_date=start_date,
        end_date=end_date,
    )
    features = build_model_features(demand)

    write_csv_atomic(features, output_path)

    summary = {
        "rows": len(features),
        "zones": int(features["zone_id"].nunique()),
        "start_timestamp": features["timestamp"].min().isoformat(),
        "end_timestamp": features["timestamp"].max().isoformat(),
        "path": str(output_path),
    }
    write_json_atomic(
        {
            "inputs": fingerprint,
            "output_sha256": file_fingerprint(output_path),
            "summary": summary,
        },
        manifest_path,
    )
    return {**summary, "status": "rebuilt"}
