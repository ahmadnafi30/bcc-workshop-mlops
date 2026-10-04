import pandas as pd

LAG_HOURS = [1, 2, 3, 24, 168]
ROLLING_WINDOWS = [3, 6, 24]

MODEL_FEATURE_COLUMNS = [
    "zone_id",
    "hour",
    "day_of_week",
    "is_weekend",
    "lag_1h",
    "lag_2h",
    "lag_3h",
    "lag_24h",
    "lag_168h",
    "rolling_mean_3h",
    "rolling_mean_6h",
    "rolling_mean_24h",
]


# cek schema minimum sebelum hourly demand dipakai buat feature engineering
def validate_demand_columns(demand: pd.DataFrame) -> None:
    # timestamp, zone, dan trip_count wajib ada karena semua feature dibangun dari sini
    required_columns = {"timestamp", "zone_id", "trip_count"}
    missing_columns = required_columns.difference(demand.columns)

    if missing_columns:
        raise ValueError(
            "hourly demand kehilangan kolom: "
            + ", ".join(sorted(missing_columns))
        )


# tambahin feature kalender supaya model bisa nangkep pattern jam dan hari
def add_calendar_features(demand: pd.DataFrame) -> pd.DataFrame:
    # copy dataframe biar function ini nggak ngubah object input dari luar
    features = demand.copy()
    features["hour"] = features["timestamp"].dt.hour.astype("int8")
    features["day_of_week"] = features["timestamp"].dt.dayofweek.astype("int8")
    features["is_weekend"] = (
        features["day_of_week"].isin([5, 6]).astype("int8")
    )

    return features


# tambahin historical demand dari beberapa jarak waktu sebelumnya
def add_lag_features(demand: pd.DataFrame) -> pd.DataFrame:
    # shift dilakukan per zone supaya demand satu zone nggak nyampur sama zone lain
    features = demand.copy()
    grouped = features.groupby("zone_id", sort=False)["trip_count"]

    for lag in LAG_HOURS:
        features[f"lag_{lag}h"] = grouped.shift(lag)

    return features


# tambahin rolling average yang cuma ngelihat demand sebelum target hour
def add_rolling_features(demand: pd.DataFrame) -> pd.DataFrame:
    # shift satu jam dulu supaya rolling window nggak pernah ikut lihat target sekarang
    features = demand.copy()
    previous_demand = features.groupby(
        "zone_id",
        sort=False,
    )["trip_count"].shift(1)

    # rolling dihitung per zone dengan minimum history sesuai panjang window
    for window in ROLLING_WINDOWS:
        features[f"rolling_mean_{window}h"] = (
            previous_demand.groupby(features["zone_id"], sort=False)
            .transform(
                lambda values: values.rolling(
                    window=window,
                    min_periods=window,
                ).mean()
            )
        )

    return features


# ubah hourly demand jadi dataset model-ready tanpa bocorin future information
def build_model_features(
    demand: pd.DataFrame,
    drop_incomplete: bool = True,
) -> pd.DataFrame:
    # validasi lalu urutin data supaya shift dan rolling benar-benar mengikuti waktu
    validate_demand_columns(demand)
    features = demand.copy()
    features["timestamp"] = pd.to_datetime(
        features["timestamp"],
        errors="raise",
    )
    features = features.sort_values(
        ["zone_id", "timestamp"]
    ).reset_index(drop=True)

    # bikin calendar, lag, dan rolling feature secara bertahap biar flow-nya gampang dibaca
    features = add_calendar_features(features)
    features = add_lag_features(features)
    features = add_rolling_features(features)

    # target adalah demand pada row sekarang, semua historical feature sudah di-shift
    features["target_trip_count"] = features["trip_count"].astype("int32")

    # lag 168 jam butuh history satu minggu, jadi row warm-up dibuang untuk training
    if drop_incomplete:
        features = features.dropna(
            subset=MODEL_FEATURE_COLUMNS
        ).reset_index(drop=True)

    # zone name tetap dibawa kalau tersedia biar hasil parquet enak diinspeksi
    output_columns = ["timestamp", "zone_id"]
    if "zone" in features.columns:
        output_columns.append("zone")

    output_columns.extend(MODEL_FEATURE_COLUMNS[1:])
    output_columns.append("target_trip_count")

    return features[output_columns].sort_values(
        ["timestamp", "zone_id"]
    ).reset_index(drop=True)
