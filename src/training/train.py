from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from features.build_features import MODEL_FEATURE_COLUMNS

TRAIN_END = pd.Timestamp("2025-01-22 00:00:00")
VALIDATION_END = pd.Timestamp("2025-01-27 00:00:00")


# pisahin feature dataset berdasarkan waktu supaya future nggak bocor ke training
def split_train_validation(
    features: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # pastiin timestamp sudah jadi datetime sebelum bikin time-based mask
    data = features.copy()
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        errors="raise",
    )

    # training pakai row sebelum 22 January, validation pakai 22-26 January
    train = data.loc[data["timestamp"] < TRAIN_END].copy()
    validation = data.loc[
        (data["timestamp"] >= TRAIN_END)
        & (data["timestamp"] < VALIDATION_END)
    ].copy()

    if train.empty:
        raise ValueError("training split kosong")

    if validation.empty:
        raise ValueError("validation split kosong")

    return train, validation


# siapin dataframe feature sesuai tipe yang diharapkan model
def prepare_model_input(data: pd.DataFrame) -> pd.DataFrame:
    # zone_id adalah category, bukan angka yang punya urutan besar-kecil
    X = data[MODEL_FEATURE_COLUMNS].copy()
    X["zone_id"] = X["zone_id"].astype("category")

    return X


# train gradient boosting dari model-ready features yang sudah bebas leakage
def train_hist_gradient_boosting(
    train_data: pd.DataFrame,
) -> HistGradientBoostingRegressor:
    # pisahin feature dan target biar input model explicit dan gampang dibaca
    X_train = prepare_model_input(train_data)
    y_train = train_data["target_trip_count"]

    # config sengaja ringan supaya tetap nyaman dijalankan di laptop workshop
    model = HistGradientBoostingRegressor(
        categorical_features="from_dtype",
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=31,
        l2_regularization=0.1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    return model


# simpan model bareng daftar feature supaya inference nanti pakai urutan yang sama
def save_model_bundle(
    model: HistGradientBoostingRegressor,
    output_path: Path,
) -> Path:
    # bundle sederhana ini nanti bakal digantikan model registry waktu masuk MLflow
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "feature_columns": MODEL_FEATURE_COLUMNS,
            "categorical_features": ["zone_id"],
        },
        output_path,
    )

    return output_path
