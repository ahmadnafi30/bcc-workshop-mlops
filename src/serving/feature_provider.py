from datetime import datetime
from pathlib import Path

import pandas as pd

from features.build_features import MODEL_FEATURE_COLUMNS

MAX_LOOKBACK_HOURS = 168


# pastiin target time pas di awal jam karena model kita forecast per hour
def validate_target_datetime(target_datetime: datetime) -> None:
    # timezone-aware input ditolak dulu supaya nggak ambigu sama timestamp lokal NYC
    if target_datetime.tzinfo is not None:
        raise ValueError("target_datetime harus tanpa timezone dan dianggap sebagai waktu lokal NYC")

    if (
        target_datetime.minute != 0
        or target_datetime.second != 0
        or target_datetime.microsecond != 0
    ):
        raise ValueError("target_datetime harus pas di awal jam, contoh 2025-01-28T18:00:00")


# load history satu zone dari processed demand sebelum target hour
def load_zone_history(
    demand_dir: Path,
    zone_id: int,
    target_datetime: datetime,
) -> pd.Series:
    # kita butuh history sampai 168 jam karena feature terjauh adalah lag_168h
    validate_target_datetime(target_datetime)

    target = pd.Timestamp(target_datetime)
    history_start = target - pd.Timedelta(hours=MAX_LOOKBACK_HOURS)
    history_end = target - pd.Timedelta(hours=1)

    frames = []

    # processed demand disimpan per hari, jadi baca file yang overlap dengan lookback window
    for day in pd.date_range(history_start.date(), history_end.date(), freq="D"):
        path = Path(demand_dir) / f"{day.date().isoformat()}.parquet"

        if not path.exists():
            raise FileNotFoundError(
                f"processed demand belum ada untuk {day.date().isoformat()}: {path}"
            )

        frames.append(
            pd.read_parquet(
                path,
                columns=["timestamp", "zone_id", "trip_count"],
            )
        )

    history = pd.concat(frames, ignore_index=True)
    history["timestamp"] = pd.to_datetime(history["timestamp"], errors="raise")

    # ambil satu zone lalu keep cuma jam yang benar-benar boleh dilihat sebelum target
    zone_history = history.loc[
        (history["zone_id"] == zone_id)
        & (history["timestamp"] >= history_start)
        & (history["timestamp"] <= history_end),
        ["timestamp", "trip_count"],
    ].copy()

    if zone_history.empty:
        raise ValueError(f"nggak ada history untuk zone_id {zone_id}")

    # expected index dipakai buat detect history bolong sebelum feature dihitung
    expected_index = pd.date_range(
        history_start,
        history_end,
        freq="h",
    )

    series = (
        zone_history.drop_duplicates("timestamp", keep="last")
        .set_index("timestamp")["trip_count"]
        .reindex(expected_index)
    )

    if series.isna().any():
        missing = series[series.isna()].index[:5]
        missing_text = ", ".join(timestamp.isoformat() for timestamp in missing)
        raise ValueError(
            "history demand belum lengkap untuk target ini. "
            f"contoh timestamp yang missing: {missing_text}"
        )

    return series.astype("float64")


# bikin satu row model input dari historical demand yang tersedia sebelum target hour
def build_online_features(
    demand_dir: Path,
    zone_id: int,
    target_datetime: datetime,
) -> pd.DataFrame:
    # history strict sebelum target bikin online feature ini nggak bocor future information
    history = load_zone_history(
        demand_dir=demand_dir,
        zone_id=zone_id,
        target_datetime=target_datetime,
    )
    target = pd.Timestamp(target_datetime)

    # lag feature tinggal ambil posisi jam yang sesuai dari history
    values = {
        "zone_id": zone_id,
        "hour": target.hour,
        "day_of_week": target.dayofweek,
        "is_weekend": int(target.dayofweek in [5, 6]),
        "lag_1h": float(history.loc[target - pd.Timedelta(hours=1)]),
        "lag_2h": float(history.loc[target - pd.Timedelta(hours=2)]),
        "lag_3h": float(history.loc[target - pd.Timedelta(hours=3)]),
        "lag_24h": float(history.loc[target - pd.Timedelta(hours=24)]),
        "lag_168h": float(history.loc[target - pd.Timedelta(hours=168)]),
        "rolling_mean_3h": float(history.tail(3).mean()),
        "rolling_mean_6h": float(history.tail(6).mean()),
        "rolling_mean_24h": float(history.tail(24).mean()),
    }

    # urutan kolom disamakan dengan training supaya model input selalu konsisten
    return pd.DataFrame([values], columns=MODEL_FEATURE_COLUMNS)
