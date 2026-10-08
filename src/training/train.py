from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from features.build_features import MODEL_FEATURE_COLUMNS

DEFAULT_VALIDATION_DAYS = 5

HIST_GRADIENT_BOOSTING_PARAMS = {
    "loss": "poisson",
    "learning_rate": 0.05,
    "max_iter": 200,
    "max_leaf_nodes": 31,
    "l2_regularization": 0.1,
    "random_state": 42,
}


# pisahin feature dataset berdasarkan waktu supaya future nggak bocor ke training
def split_train_validation(
    features: pd.DataFrame,
    validation_days: int = DEFAULT_VALIDATION_DAYS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # pastiin timestamp sudah jadi datetime sebelum bikin time-based mask
    data = features.copy()
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        errors="raise",
    )

    # validation selalu pakai beberapa hari paling akhir dari snapshot
    validation_end = data["timestamp"].max().normalize() + pd.Timedelta(days=1)
    validation_start = validation_end - pd.Timedelta(days=validation_days)

    train = data.loc[data["timestamp"] < validation_start].copy()
    validation = data.loc[
        (data["timestamp"] >= validation_start) & (data["timestamp"] < validation_end)
    ].copy()

    if train.empty:
        raise ValueError("training split kosong")

    if validation.empty:
        raise ValueError("validation split kosong")

    return train, validation


# siapin dataframe feature dalam urutan yang selalu sama buat fit dan predict
def prepare_model_input(data: pd.DataFrame) -> pd.DataFrame:
    # zone_id tetap numeric di dataframe, tapi model bakal treat kolom ini sebagai categorical
    return data[MODEL_FEATURE_COLUMNS].copy()


# train gradient boosting dari model-ready features yang sudah bebas leakage
def train_hist_gradient_boosting(
    train_data: pd.DataFrame,
    model_params: dict | None = None,
    cpu_threads: int = 2,
) -> HistGradientBoostingRegressor:
    if cpu_threads < 1:
        raise ValueError("cpu_threads harus minimal 1")
    params = {**HIST_GRADIENT_BOOSTING_PARAMS, **(model_params or {})}
    # pisahin feature dan target biar input model explicit dan gampang dibaca
    X_train = prepare_model_input(train_data)
    y_train = train_data["target_trip_count"]
    target_values = y_train.to_numpy(dtype=float)

    if not np.isfinite(target_values).all():
        raise ValueError("target_trip_count harus finite")
    if (target_values < 0).any():
        raise ValueError("loss poisson memerlukan target_trip_count tidak negatif")

    # zone_id disebut explicit sebagai categorical karena id zone bukan nilai ordinal
    model = HistGradientBoostingRegressor(
        categorical_features=["zone_id"],
        **params,
    )
    # batas thread eksplisit membuat training konsisten pada laptop workshop.
    with threadpool_limits(limits=cpu_threads):
        model.fit(X_train, y_train)

    return model


# simpan model bareng daftar feature supaya inference nanti pakai urutan yang sama
def save_model_bundle(
    model: HistGradientBoostingRegressor,
    output_path: Path,
) -> Path:
    # bundle sederhana ini tetap dipakai buat manual flow sebelum pindah penuh ke registry
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
