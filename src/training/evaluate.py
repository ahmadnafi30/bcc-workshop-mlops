import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


# hitung metric regression yang bakal dipakai konsisten di baseline dan model utama
def calculate_regression_metrics(
    y_true,
    y_pred,
) -> dict[str, float]:
    # MAE jadi metric utama, RMSE dipakai buat lihat error besar lebih sensitif
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    return {
        "mae": float(mae),
        "rmse": float(rmse),
    }


# pakai demand pada jam yang sama kemarin sebagai baseline paling sederhana
def evaluate_naive_24h(validation_data) -> dict[str, float]:
    # lag_24h sudah tersedia dari feature engineering jadi baseline nggak perlu training
    return calculate_regression_metrics(
        y_true=validation_data["target_trip_count"],
        y_pred=validation_data["lag_24h"],
    )
