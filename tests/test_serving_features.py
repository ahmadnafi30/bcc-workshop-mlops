from datetime import datetime

import pandas as pd
import pytest

from serving.feature_provider import build_online_features


# bikin processed demand harian kecil buat test online feature tanpa dependency ke TLC
def write_daily_demand(
    demand_dir,
    day: str,
    zone_id: int = 161,
) -> None:
    # trip_count sengaja dibuat dari hour offset supaya expected lag gampang dicek
    timestamps = pd.date_range(
        f"{day} 00:00:00",
        periods=24,
        freq="h",
    )
    base = int((pd.Timestamp(day) - pd.Timestamp("2025-01-01")).days * 24)

    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "zone_id": zone_id,
            "trip_count": [base + hour for hour in range(24)],
        }
    )

    demand_dir.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(demand_dir / f"{day}.parquet", index=False)


# pastikan online feature cuma ngelihat history sebelum target hour
def test_build_online_features_uses_only_past_history(tmp_path) -> None:
    # target Jan 8 jam 18 butuh history dari Jan 1 jam 18 sampai Jan 8 jam 17
    demand_dir = tmp_path / "demand"

    for day in pd.date_range("2025-01-01", "2025-01-08", freq="D"):
        write_daily_demand(demand_dir, day.date().isoformat())

    features = build_online_features(
        demand_dir=demand_dir,
        zone_id=161,
        target_datetime=datetime(2025, 1, 8, 18, 0, 0),
    )

    row = features.iloc[0]

    assert row["lag_1h"] == 185
    assert row["lag_2h"] == 184
    assert row["lag_3h"] == 183
    assert row["lag_24h"] == 162
    assert row["lag_168h"] == 18
    assert row["rolling_mean_3h"] == 184
    assert row["rolling_mean_6h"] == 182.5
    assert row["rolling_mean_24h"] == 173.5


# pastikan target yang bukan awal jam ditolak sebelum baca data
def test_build_online_features_rejects_non_hour_target(tmp_path) -> None:
    with pytest.raises(ValueError, match="awal jam"):
        build_online_features(
            demand_dir=tmp_path,
            zone_id=161,
            target_datetime=datetime(2025, 1, 8, 18, 30, 0),
        )
