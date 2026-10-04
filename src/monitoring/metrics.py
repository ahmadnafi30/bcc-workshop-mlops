import json
from pathlib import Path

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

API_REQUESTS = Counter(
    "taxi_api_requests_total",
    "total request yang diterima FastAPI",
    ["method", "path", "status"],
)
API_REQUEST_LATENCY = Histogram(
    "taxi_api_request_duration_seconds",
    "durasi request FastAPI dalam detik",
    ["method", "path"],
)
PREDICTIONS = Counter(
    "taxi_predictions_total",
    "total prediction yang berhasil dibuat",
    ["model_version"],
)
PREDICTION_VALUE = Histogram(
    "taxi_prediction_trip_count",
    "distribusi predicted pickup count",
    buckets=(0, 10, 25, 50, 100, 200, 400, 800, 1600),
)
MODEL_VERSION = Gauge(
    "taxi_model_version_info",
    "model version yang terakhir dipakai buat prediction",
    ["model_name", "model_version", "model_alias"],
)
RECENT_MAE = Gauge(
    "taxi_model_recent_mae",
    "MAE terbaru dari prediction yang ground truth-nya sudah tersedia",
)
REFERENCE_MAE = Gauge(
    "taxi_model_reference_mae",
    "validation MAE dari champion model saat training",
)
RETRAIN_RECOMMENDED = Gauge(
    "taxi_model_retrain_recommended",
    "1 kalau recent MAE sudah melewati retraining threshold",
)
EVALUATED_PREDICTIONS = Gauge(
    "taxi_model_evaluated_predictions",
    "jumlah prediction yang dipakai di performance window terbaru",
)

KNOWN_PATHS = {
    "/health",
    "/model-info",
    "/predict",
    "/metrics",
    "/docs",
    "/openapi.json",
}


# rapihin request path supaya label prometheus nggak punya cardinality liar
def normalize_request_path(path: str) -> str:
    if path in KNOWN_PATHS:
        return path

    return "other"


# catat satu prediction yang berhasil dibuat
def observe_prediction(result: dict) -> None:
    # model version cukup kecil cardinality-nya dan useful buat lihat rollout model
    model_version = str(result["model_version"])
    PREDICTIONS.labels(model_version=model_version).inc()
    PREDICTION_VALUE.observe(float(result["predicted_trip_count"]))

    MODEL_VERSION.labels(
        model_name=str(result["model_name"]),
        model_version=model_version,
        model_alias=str(result["model_alias"]),
    ).set(1)


# refresh gauge model performance dari summary file hasil evaluation job
def refresh_performance_metrics(summary_path: Path) -> None:
    # file summary boleh belum ada saat API baru pertama kali start
    summary_path = Path(summary_path)

    if not summary_path.exists():
        return

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    if summary.get("recent_mae") is not None:
        RECENT_MAE.set(float(summary["recent_mae"]))

    if summary.get("reference_mae") is not None:
        REFERENCE_MAE.set(float(summary["reference_mae"]))

    RETRAIN_RECOMMENDED.set(
        1 if summary.get("retrain_recommended", False) else 0
    )
    EVALUATED_PREDICTIONS.set(int(summary.get("evaluation_count", 0)))


# render semua metric dalam prometheus exposition format
def render_metrics(summary_path: Path) -> tuple[bytes, str]:
    # model performance gauge direfresh tepat sebelum prometheus scrape endpoint
    refresh_performance_metrics(summary_path)

    return generate_latest(), CONTENT_TYPE_LATEST
