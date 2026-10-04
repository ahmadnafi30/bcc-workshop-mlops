from fastapi.testclient import TestClient

from api.dependencies import get_predictor
from api.main import app


class FakePredictor:
    # fake model info bikin API test nggak perlu nyalain MLflow
    def get_model_info(self):
        return {
            "model_name": "taxi-model-test",
            "model_version": "3",
            "model_alias": "champion",
            "run_id": "run-test",
            "model_uri": "models:/taxi-model-test@champion",
        }

    # fake prediction dipakai buat ngetes contract endpoint
    def predict(self, zone_id, target_datetime):
        return {
            "zone_id": zone_id,
            "target_datetime": target_datetime,
            "predicted_trip_count": 88.25,
            **self.get_model_info(),
        }


# bikin TestClient dengan dependency override biar test terisolasi dari registry
def make_client() -> TestClient:
    app.dependency_overrides[get_predictor] = lambda: FakePredictor()
    return TestClient(app)


# pastikan health endpoint bisa dipakai tanpa model registry
def test_health_endpoint() -> None:
    client = make_client()

    try:
        response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# pastikan model info endpoint expose champion metadata
def test_model_info_endpoint() -> None:
    client = make_client()

    try:
        response = client.get("/model-info")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["model_version"] == "3"
    assert response.json()["model_alias"] == "champion"


# pastikan predict endpoint punya request dan response contract yang jelas
def test_predict_endpoint() -> None:
    client = make_client()

    try:
        response = client.post(
            "/predict",
            json={
                "zone_id": 161,
                "target_datetime": "2025-01-28T18:00:00",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["predicted_trip_count"] == 88.25
    assert response.json()["model_alias"] == "champion"


# pastikan target di tengah jam ditolak langsung oleh schema API
def test_predict_rejects_non_hour_target() -> None:
    client = make_client()

    try:
        response = client.post(
            "/predict",
            json={
                "zone_id": 161,
                "target_datetime": "2025-01-28T18:30:00",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
