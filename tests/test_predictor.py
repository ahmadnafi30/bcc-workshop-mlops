from datetime import datetime

import pandas as pd

from serving.predictor import TaxiDemandPredictor


class FakeModel:
    # balikin prediction fixed supaya test fokus ke serving flow
    def predict(self, features):
        assert list(features.columns)
        return [123.5]


class FakeModelLoader:
    # fake loader nggak butuh MLflow server untuk unit test
    def get_model(self):
        return FakeModel(), {
            "model_name": "taxi-model-test",
            "model_version": "7",
            "model_alias": "champion",
            "run_id": "run-test",
            "model_uri": "models:/taxi-model-test@champion",
        }

    # metadata ini dipakai /model-info dan predictor wrapper
    def get_model_info(self):
        return self.get_model()[1]


# tulis delapan hari history supaya predictor punya full lag_168h
def write_history(demand_dir) -> None:
    for day in pd.date_range("2025-01-01", "2025-01-08", freq="D"):
        timestamps = pd.date_range(
            day,
            periods=24,
            freq="h",
        )
        base = int((day - pd.Timestamp("2025-01-01")).days * 24)

        frame = pd.DataFrame(
            {
                "timestamp": timestamps,
                "zone_id": 161,
                "trip_count": [base + hour for hour in range(24)],
            }
        )

        demand_dir.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(
            demand_dir / f"{day.date().isoformat()}.parquet",
            index=False,
        )


# pastikan predictor gabungin online feature, model output, dan registry metadata
def test_predictor_returns_prediction_with_model_info(tmp_path) -> None:
    demand_dir = tmp_path / "demand"
    write_history(demand_dir)

    predictor = TaxiDemandPredictor(
        demand_dir=demand_dir,
        model_loader=FakeModelLoader(),
    )

    result = predictor.predict(
        zone_id=161,
        target_datetime=datetime(2025, 1, 8, 18, 0, 0),
    )

    assert result["predicted_trip_count"] == 123.5
    assert result["model_version"] == "7"
    assert result["model_alias"] == "champion"
