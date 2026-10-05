import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from features.build_features import MODEL_FEATURE_COLUMNS
from tracking.mlflow_tracking import configure_mlflow, log_sklearn_run
from training.train import prepare_model_input, train_hist_gradient_boosting


def test_logged_gradient_boosting_model_can_be_loaded(tmp_path, monkeypatch) -> None:
    # pakai model asli dan store lokal agar error serialisasi ikut terdeteksi
    rows = 80
    data = pd.DataFrame(
        {column: np.arange(rows) + 10 for column in MODEL_FEATURE_COLUMNS}
    )
    data["zone_id"] = [161 + i % 2 for i in range(rows)]
    data["hour"] = np.arange(rows) % 24
    data["day_of_week"] = np.arange(rows) % 7
    data["is_weekend"] = (data["day_of_week"] >= 5).astype(int)
    data["target_trip_count"] = np.arange(rows) + 11
    model = train_hist_gradient_boosting(data)
    inputs = prepare_model_input(data).head(5)

    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", tracking_uri)
    monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "serialization-regression")
    mlflow.MlflowClient(tracking_uri=tracking_uri).create_experiment(
        "serialization-regression",
        artifact_location=(tmp_path / "artifacts").as_uri(),
    )
    previous_tracking_uri = mlflow.get_tracking_uri()
    try:
        configure_mlflow()
        result = log_sklearn_run(
            model=model,
            model_params={},
            metrics={"mae": 1.0},
            input_example=inputs,
            train_rows=rows,
            validation_rows=5,
            dataset_info={
                "name": "test.parquet",
                "sha256": "0" * 64,
                "rows": rows,
                "zones": 2,
                "start_timestamp": "2025-01-08 00:00:00",
                "end_timestamp": "2025-01-26 23:00:00",
            },
        )

        loaded_model = mlflow.sklearn.load_model(result["model_uri"])
        np.testing.assert_allclose(loaded_model.predict(inputs), model.predict(inputs))
    finally:
        mlflow.set_tracking_uri(previous_tracking_uri)
