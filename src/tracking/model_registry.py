import os
from datetime import datetime, timezone

import mlflow
import mlflow.sklearn
from mlflow import MlflowClient

from tracking.mlflow_tracking import MODEL_ARTIFACT_NAME

DEFAULT_REGISTERED_MODEL_NAME = "taxi-demand-forecasting-model"


# ambil nama registered model dari argumen, env, atau default workshop
def resolve_model_name(model_name: str | None = None) -> str:
    # satu resolver dipakai semua script supaya nama model tetap konsisten
    return (
        model_name
        or os.getenv("MLFLOW_REGISTERED_MODEL_NAME")
        or DEFAULT_REGISTERED_MODEL_NAME
    )


# bikin uri registry berbasis alias supaya serving nggak perlu tahu version number
def build_registered_model_uri(
    alias: str = "champion",
    model_name: str | None = None,
) -> str:
    # alias bikin consumer cukup tahu role model, bukan version fisiknya
    resolved_model_name = resolve_model_name(model_name)
    return f"models:/{resolved_model_name}@{alias}"


# register model artifact dari sebuah experiment run lalu kasih alias candidate
def register_run_model(
    run_id: str,
    alias: str = "challenger",
    model_name: str | None = None,
) -> dict[str, str]:
    # model artifact yang dilog saat training bisa direferensikan langsung dari run id
    resolved_model_name = resolve_model_name(model_name)
    model_uri = f"runs:/{run_id}/{MODEL_ARTIFACT_NAME}"

    # register_model otomatis bikin registered model baru atau version berikutnya
    model_version = mlflow.register_model(
        model_uri=model_uri,
        name=resolved_model_name,
    )

    client = MlflowClient()

    # tags nyimpen context minimum sebelum candidate direview atau dipromote
    client.set_model_version_tag(
        resolved_model_name,
        model_version.version,
        "validation_status",
        "pending",
    )
    client.set_model_version_tag(
        resolved_model_name,
        model_version.version,
        "source_run_id",
        run_id,
    )

    # challenger jadi pointer mutable ke candidate terbaru yang lagi dievaluasi
    if alias:
        client.set_registered_model_alias(
            resolved_model_name,
            alias,
            model_version.version,
        )

    return {
        "model_name": resolved_model_name,
        "version": str(model_version.version),
        "alias": alias,
        "model_uri": build_registered_model_uri(
            alias=alias,
            model_name=resolved_model_name,
        ),
    }


# promote model version yang sudah direview ke alias yang dipakai production
def promote_model_version(
    version: str,
    alias: str = "champion",
    model_name: str | None = None,
) -> dict[str, str]:
    # promotion explicit supaya candidate nggak langsung jadi production tanpa review
    resolved_model_name = resolve_model_name(model_name)
    client = MlflowClient()

    # get dulu biar version invalid gagal sebelum alias production diubah
    client.get_model_version(
        name=resolved_model_name,
        version=version,
    )

    client.set_registered_model_alias(
        resolved_model_name,
        alias,
        version,
    )

    # tag approval bikin history registry lebih gampang dibaca dari UI
    client.set_model_version_tag(
        resolved_model_name,
        version,
        "validation_status",
        "approved",
    )
    client.set_model_version_tag(
        resolved_model_name,
        version,
        "promoted_at",
        datetime.now(timezone.utc).isoformat(),
    )

    return {
        "model_name": resolved_model_name,
        "version": str(version),
        "alias": alias,
        "model_uri": build_registered_model_uri(
            alias=alias,
            model_name=resolved_model_name,
        ),
    }


# load model lewat alias supaya caller nggak hard-code version registry
def load_model_by_alias(
    alias: str = "champion",
    model_name: str | None = None,
):
    # function ini nanti bisa dipakai langsung sama FastAPI service
    model_uri = build_registered_model_uri(
        alias=alias,
        model_name=model_name,
    )

    return mlflow.sklearn.load_model(model_uri)
