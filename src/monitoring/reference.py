from mlflow import MlflowClient

from tracking.mlflow_tracking import configure_mlflow
from tracking.model_registry import resolve_model_name


# ambil validation metric dari champion run sebagai reference performance
def get_champion_reference(
    alias: str = "champion",
    model_name: str | None = None,
) -> dict[str, str | float]:
    # registry dan experiment metadata dibaca dari MLflow server yang sama
    configure_mlflow()
    client = MlflowClient()
    resolved_model_name = resolve_model_name(model_name)

    version = client.get_model_version_by_alias(
        name=resolved_model_name,
        alias=alias,
    )

    if not version.run_id:
        raise ValueError("champion model version nggak punya source run id")

    run = client.get_run(version.run_id)

    if "mae" not in run.data.metrics:
        raise ValueError("champion run nggak punya validation metric mae")

    return {
        "model_name": resolved_model_name,
        "model_version": str(version.version),
        "run_id": str(version.run_id),
        "reference_mae": float(run.data.metrics["mae"]),
        "reference_rmse": float(run.data.metrics.get("rmse", 0.0)),
    }
