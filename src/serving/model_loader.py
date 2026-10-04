import mlflow.sklearn
from mlflow import MlflowClient

from tracking.mlflow_tracking import configure_mlflow
from tracking.model_registry import (
    build_registered_model_uri,
    resolve_model_name,
)


class RegistryModelLoader:
    # siapin loader yang selalu ngikutin satu alias di MLflow Model Registry
    def __init__(
        self,
        alias: str = "champion",
        model_name: str | None = None,
    ) -> None:
        self.alias = alias
        self.model_name = resolve_model_name(model_name)
        self._model = None
        self._loaded_version = None

    # ambil metadata model version yang sekarang ditunjuk sama alias
    def get_model_info(self) -> dict[str, str]:
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
            "model_uri": build_registered_model_uri(
                alias=self.alias,
                model_name=self.model_name,
            ),
        }

    # load model kalau belum ada atau kalau alias pindah ke version yang lebih baru
    def get_model(self):
        # version dicek setiap request supaya champion update nggak butuh ubah application code
        info = self.get_model_info()

        if (
            self._model is None
            or self._loaded_version != info["model_version"]
        ):
            self._model = mlflow.sklearn.load_model(info["model_uri"])
            self._loaded_version = info["model_version"]

        return self._model, info
