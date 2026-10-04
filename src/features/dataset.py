from datetime import date
from pathlib import Path

import pandas as pd

from features.build_features import build_model_features


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
        path = Path(demand_dir) / f"{target_date.isoformat()}.parquet"

        if not path.exists():
            missing_dates.append(target_date.isoformat())
            continue

        frames.append(pd.read_parquet(path))

    # history bolong bisa bikin lag salah, jadi lebih aman fail daripada lanjut diam-diam
    if missing_dates:
        preview = ", ".join(missing_dates[:5])
        suffix = "..." if len(missing_dates) > 5 else ""
        raise FileNotFoundError(
            f"processed demand belum lengkap: {preview}{suffix}"
        )

    if not frames:
        raise ValueError("nggak ada processed demand yang bisa digabung")

    return pd.concat(frames, ignore_index=True)


# gabung processed demand lalu tulis ulang model-ready feature dataset
def build_feature_dataset(
    demand_dir: Path,
    output_path: Path,
    start_date: date,
    end_date: date,
) -> dict[str, int | str]:
    # feature selalu dibangun dari full history sampai end date supaya lag tetap konsisten
    demand = load_demand_range(
        demand_dir=demand_dir,
        start_date=start_date,
        end_date=end_date,
    )
    features = build_model_features(demand)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(output_path, index=False)

    return {
        "rows": len(features),
        "zones": int(features["zone_id"].nunique()),
        "start_timestamp": features["timestamp"].min().isoformat(),
        "end_timestamp": features["timestamp"].max().isoformat(),
        "path": str(output_path),
    }
