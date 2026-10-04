import pandas as pd

from features.build_features import build_model_features


# pastikan lag dan rolling feature cuma ngelihat historical demand sebelum target hour
def test_build_model_features_avoids_future_leakage() -> None:
    # bikin 200 jam demand berurutan supaya expected lag gampang dicek manual
    timestamps = pd.date_range(
        "2025-01-01 00:00:00",
        periods=200,
        freq="h",
    )
    demand = pd.DataFrame(
        {
            "timestamp": timestamps,
            "zone_id": 161,
            "zone": "Midtown Center",
            "trip_count": range(200),
        }
    )

    # drop_incomplete bikin row pertama yang keluar sudah punya full 168 jam history
    features = build_model_features(demand, drop_incomplete=True)
    first = features.iloc[0]

    assert first["timestamp"] == pd.Timestamp("2025-01-08 00:00:00")
    assert first["target_trip_count"] == 168
    assert first["lag_1h"] == 167
    assert first["lag_24h"] == 144
    assert first["lag_168h"] == 0

    # rolling 3 jam untuk target 168 cuma boleh pakai 165, 166, dan 167
    assert first["rolling_mean_3h"] == 166


# pastikan shift dilakukan per zone dan nggak nyampur history antar lokasi
def test_build_model_features_keeps_zone_history_separate() -> None:
    # dua zone punya pola demand yang sengaja beda jauh biar leakage antar zone kelihatan
    timestamps = pd.date_range(
        "2025-01-01 00:00:00",
        periods=170,
        freq="h",
    )
    zone_a = pd.DataFrame(
        {
            "timestamp": timestamps,
            "zone_id": 161,
            "trip_count": range(170),
        }
    )
    zone_b = pd.DataFrame(
        {
            "timestamp": timestamps,
            "zone_id": 162,
            "trip_count": range(1000, 1170),
        }
    )

    features = build_model_features(
        pd.concat([zone_a, zone_b], ignore_index=True)
    )

    first_zone_b = features.loc[features["zone_id"] == 162].iloc[0]

    assert first_zone_b["lag_1h"] == 1167
    assert first_zone_b["lag_168h"] == 1000
