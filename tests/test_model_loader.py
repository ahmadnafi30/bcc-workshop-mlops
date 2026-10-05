from types import SimpleNamespace
from unittest.mock import Mock

from serving.model_loader import RegistryModelLoader


# pergantian alias tidak boleh mengubah artifact yang sudah diresolve versinya
def test_loader_pins_artifact_to_resolved_version(monkeypatch):
    client = Mock()
    client.get_model_version_by_alias.return_value = SimpleNamespace(version="1", run_id="run-1")
    monkeypatch.setattr("serving.model_loader.configure_mlflow", lambda: None)
    monkeypatch.setattr("serving.model_loader.MlflowClient", lambda: client)
    loaded_model = object()

    def load_model(uri):
        # registry sudah berubah, tetapi URI immutable tetap harus menunjuk version 1
        client.get_model_version_by_alias.return_value = SimpleNamespace(
            version="2", run_id="run-2"
        )
        assert uri == "models:/taxi-test/1"
        return loaded_model

    load = Mock(side_effect=load_model)
    monkeypatch.setattr("serving.model_loader.mlflow.sklearn.load_model", load)
    loader = RegistryModelLoader(model_name="taxi-test")

    model, info = loader.get_model()
    assert model is loaded_model
    assert info["model_version"] == "1"
    assert info["run_id"] == "run-1"
    assert info["model_uri"] == "models:/taxi-test/1"
    assert loader.get_model() == (loaded_model, info)
    load.assert_called_once()


# saat cache expired model dan metadata ikut berganti sebagai satu pasangan
def test_loader_refreshes_model_and_metadata_together(monkeypatch):
    client = Mock()
    client.get_model_version_by_alias.side_effect = [
        SimpleNamespace(version="1", run_id="run-1"),
        SimpleNamespace(version="2", run_id="run-2"),
    ]
    monkeypatch.setattr("serving.model_loader.configure_mlflow", lambda: None)
    monkeypatch.setattr("serving.model_loader.MlflowClient", lambda: client)
    load = Mock(side_effect=lambda uri: uri)
    monkeypatch.setattr("serving.model_loader.mlflow.sklearn.load_model", load)
    loader = RegistryModelLoader(model_name="taxi-test", refresh_interval_seconds=0)

    first_model, first_info = loader.get_model()
    second_model, second_info = loader.get_model()

    assert (first_model, first_info["model_version"]) == ("models:/taxi-test/1", "1")
    assert (second_model, second_info["model_version"]) == ("models:/taxi-test/2", "2")
