import pandas as pd

from features.build_features import MODEL_FEATURE_COLUMNS
from training.evaluate import calculate_regression_metrics
from training.train import (
    prepare_model_input,
    split_train_validation,
    train_hist_gradient_boosting,
)


# pastikan metric regression menghasilkan nilai yang gampang diverifikasi manual
def test_calculate_regression_metrics() -> None:
    # error absolute-nya 0, 1, 2 jadi MAE harus tepat satu
    metrics = calculate_regression_metrics(
        y_true=[10, 10, 10],
        y_pred=[10, 11, 12],
    )

    assert metrics["mae"] == 1.0
    assert round(metrics["rmse"], 6) == round((5 / 3) ** 0.5, 6)


# pastikan train dan validation benar-benar dipisah berdasarkan timestamp
def test_split_train_validation_uses_time_order() -> None:
    # bikin row di dua sisi boundary biar split-nya gampang dicek
    features = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2025-01-21 23:00:00",
                    "2025-01-22 00:00:00",
                    "2025-01-26 23:00:00",
                ]
            ),
            "target_trip_count": [10, 20, 30],
        }
    )

    train, validation = split_train_validation(features)

    assert len(train) == 1
    assert len(validation) == 2
    assert train["target_trip_count"].tolist() == [10]
    assert validation["target_trip_count"].tolist() == [20, 30]


# pastikan validation window ikut maju kalau snapshot retraining punya tanggal lebih baru
def test_split_train_validation_moves_with_latest_snapshot_date() -> None:
    features = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2025-02-01 00:00:00",
                "2025-02-10 23:00:00",
                freq="h",
            ),
            "target_trip_count": 1,
        }
    )

    train, validation = split_train_validation(features)

    assert train["timestamp"].max() == pd.Timestamp("2025-02-05 23:00:00")
    assert validation["timestamp"].min() == pd.Timestamp("2025-02-06 00:00:00")
    assert validation["timestamp"].max() == pd.Timestamp("2025-02-10 23:00:00")


# pastikan model utama bisa fit dan predict dari schema feature yang kita sepakati
def test_hist_gradient_boosting_can_train_and_predict() -> None:
    # bikin synthetic feature dataset kecil tanpa perlu dependency ke file TLC
    rows = 80
    train_data = pd.DataFrame(
        {
            "zone_id": [161 + (i % 2) for i in range(rows)],
            "hour": [i % 24 for i in range(rows)],
            "day_of_week": [i % 7 for i in range(rows)],
            "is_weekend": [1 if i % 7 in [5, 6] else 0 for i in range(rows)],
            "lag_1h": [20 + i for i in range(rows)],
            "lag_2h": [19 + i for i in range(rows)],
            "lag_3h": [18 + i for i in range(rows)],
            "lag_24h": [10 + i for i in range(rows)],
            "lag_168h": [5 + i for i in range(rows)],
            "rolling_mean_3h": [19 + i for i in range(rows)],
            "rolling_mean_6h": [17 + i for i in range(rows)],
            "rolling_mean_24h": [12 + i for i in range(rows)],
            "target_trip_count": [21 + i for i in range(rows)],
        }
    )

    model = train_hist_gradient_boosting(train_data)
    predictions = model.predict(
        prepare_model_input(train_data).head(5)
    )

    assert len(predictions) == 5
    assert list(prepare_model_input(train_data).columns) == MODEL_FEATURE_COLUMNS
