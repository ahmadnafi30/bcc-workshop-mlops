import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from zoneinfo import ZoneInfo

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
THRESHOLD_MAE = Gauge(
    "taxi_model_threshold_mae",
    "batas MAE untuk rekomendasi retraining",
)
MIN_EVALUATION_SAMPLES = Gauge(
    "taxi_model_min_evaluation_samples",
    "minimum sample sebelum keputusan retraining boleh dibuat",
)
EVALUATION_STATUS = Gauge(
    "taxi_model_evaluation_status",
    "0 belum dievaluasi, 1 sample kurang, 2 dalam batas, 3 perlu retrain",
)
LAST_EVALUATION_TIMESTAMP = Gauge(
    "taxi_model_last_evaluation_timestamp_seconds",
    "waktu UTC saat job terakhir menghitung evaluasi",
)
LATEST_TARGET_TIMESTAMP = Gauge(
    "taxi_model_latest_target_timestamp_seconds",
    "target historical terakhir yang actual-nya sudah dievaluasi",
)
EVALUATED_MODEL_VERSION = Gauge(
    "taxi_model_evaluated_version_info",
    "model yang menjadi sumber summary evaluasi terbaru",
    ["model_name", "model_version", "run_id"],
)

LOGGER = logging.getLogger(__name__)
METRICS_LOCK = RLock()
_active_model_labels: tuple[str, str, str] | None = None

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
    global _active_model_labels

    # model version cukup kecil cardinality-nya dan useful buat lihat rollout model
    model_version = str(result["model_version"])
    PREDICTIONS.labels(model_version=model_version).inc()
    PREDICTION_VALUE.observe(float(result["predicted_trip_count"]))

    labels = (str(result["model_name"]), model_version, str(result["model_alias"]))
    with METRICS_LOCK:
        if _active_model_labels is not None and _active_model_labels != labels:
            MODEL_VERSION.labels(*_active_model_labels).set(0)

        MODEL_VERSION.labels(*labels).set(1)
        _active_model_labels = labels


# unknown harus terlihat sebagai N/A, bukan MAE nol yang seolah-olah sempurna
def _reset_performance_metrics() -> None:
    for metric in (
        RECENT_MAE,
        REFERENCE_MAE,
        THRESHOLD_MAE,
        MIN_EVALUATION_SAMPLES,
        LAST_EVALUATION_TIMESTAMP,
        LATEST_TARGET_TIMESTAMP,
    ):
        metric.set(float("nan"))

    EVALUATION_STATUS.set(0)
    EVALUATED_PREDICTIONS.set(0)
    RETRAIN_RECOMMENDED.set(0)
    EVALUATED_MODEL_VERSION.clear()


# timestamp replay adalah waktu NYC, sedangkan evaluated_at adalah waktu job UTC
def _timestamp_seconds(value: str | None, default_timezone) -> float:
    if value is None:
        return float("nan")

    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=default_timezone)

    return timestamp.timestamp()


# refresh gauge model performance dari summary file hasil evaluation job
def refresh_performance_metrics(summary_path: Path) -> None:
    summary_path = Path(summary_path)
    with METRICS_LOCK:
        # reset juga saat summary hilang, supaya metric lama tidak tertinggal
        _reset_performance_metrics()
        if not summary_path.exists():
            return

        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            count = int(summary.get("evaluation_count", 0))
            minimum = int(summary.get("min_samples", 100))
            recent_mae = float(
                summary["recent_mae"] if summary.get("recent_mae") is not None else "nan"
            )
            reference_mae = float(summary.get("reference_mae", "nan"))
            threshold_mae = float(summary.get("threshold_mae", "nan"))
            evaluated_at = (
                _timestamp_seconds(summary["evaluated_at"], timezone.utc)
                if summary.get("evaluated_at")
                else summary_path.stat().st_mtime
            )
            latest_target = _timestamp_seconds(
                summary.get("latest_target_datetime"), ZoneInfo("America/New_York")
            )
        except (OSError, ValueError, TypeError, AttributeError) as error:
            # summary invalid tidak boleh membuat scrape operational metrics ikut gagal
            LOGGER.warning("summary monitoring belum bisa dibaca: %s", error)
            return

        REFERENCE_MAE.set(reference_mae)
        THRESHOLD_MAE.set(threshold_mae)
        MIN_EVALUATION_SAMPLES.set(minimum)
        EVALUATED_PREDICTIONS.set(count)
        LAST_EVALUATION_TIMESTAMP.set(evaluated_at)
        LATEST_TARGET_TIMESTAMP.set(latest_target)

        if summary.get("model_name") and summary.get("model_version"):
            EVALUATED_MODEL_VERSION.labels(
                model_name=str(summary["model_name"]),
                model_version=str(summary["model_version"]),
                run_id=str(summary.get("run_id", "")),
            ).set(1)

        if count == 0 or summary.get("recent_mae") is None:
            return

        RECENT_MAE.set(recent_mae)
        if count < minimum:
            EVALUATION_STATUS.set(1)
        elif summary.get("retrain_recommended", False):
            EVALUATION_STATUS.set(3)
            RETRAIN_RECOMMENDED.set(1)
        else:
            EVALUATION_STATUS.set(2)


# render semua metric dalam prometheus exposition format
def render_metrics(summary_path: Path) -> tuple[bytes, str]:
    # model performance gauge direfresh tepat sebelum prometheus scrape endpoint
    with METRICS_LOCK:
        refresh_performance_metrics(summary_path)
        return generate_latest(), CONTENT_TYPE_LATEST


_reset_performance_metrics()
