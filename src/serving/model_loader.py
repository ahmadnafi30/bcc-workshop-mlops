from threading import RLock
from time import monotonic

import mlflow.sklearn
from mlflow import MlflowClient

from tracking.mlflow_tracking import configure_mlflow
from tracking.model_registry import resolve_model_name


class RegistryModelLoader:
    # siapin loader yang ngikutin alias registry tapi nggak query MLflow di setiap request
    def __init__(
        self,
        alias: str = "champion",
        model_name: str | None = None,
        refresh_interval_seconds: float = 30.0,
    ) -> None:
        self.alias = alias
        self.model_name = resolve_model_name(model_name)
        self.refresh_interval_seconds = refresh_interval_seconds
        self._model = None
        self._model_info = None
        self._loaded_version = None
        self._last_registry_check = 0.0
        self._lock = RLock()

    # query metadata model version yang sekarang ditunjuk sama alias
    def fetch_model_info(self) -> dict[str, str]:
        # client diarahkan dulu ke tracking server yang sama dengan registry
        configure_mlflow()
        client = MlflowClient()
        version = client.get_model_version_by_alias(
            name=self.model_name,
            alias=self.alias,
        )

        return {
            "model_name": self.model_name,
            "model_version": str(version.version),
            "model_alias": self.alias,
            "run_id": str(version.run_id or ""),
            # artifact dipin ke version hasil resolve, walaupun alias berubah saat load
            "model_uri": f"models:/{self.model_name}/{version.version}",
        }

    # reuse registry metadata sebentar supaya batch prediction nggak spam MLflow server
    def get_model_info(self) -> dict[str, str]:
        with self._lock:
            now = monotonic()
            cache_expired = (
                self._model_info is None
                or now - self._last_registry_check
                >= self.refresh_interval_seconds
            )

            if cache_expired:
                self._model_info = self.fetch_model_info()
                self._last_registry_check = now

            return self._model_info

    # load model kalau belum ada atau setelah alias terdeteksi pindah version
    def get_model(self):
        # model dan metadata selalu dikembalikan sebagai pasangan yang konsisten
        with self._lock:
            info = self.get_model_info()

            if (
                self._model is None
                or self._loaded_version != info["model_version"]
            ):
                self._model = mlflow.sklearn.load_model(info["model_uri"])
                self._loaded_version = info["model_version"]

            return self._model, info
