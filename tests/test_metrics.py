import json
import math
from datetime import datetime, timezone

import pandas as pd
import pytest
from prometheus_client import REGISTRY

from monitoring import metrics
from monitoring.performance import save_performance_artifacts, summarize_performance


# test lewat summary dan exposition yang sama dengan job evaluasi dan /metrics
def write_summary(tmp_path, count=100, error=15.0):
    evaluations = pd.DataFrame(
        {
            "target_datetime": pd.date_range("2025-01-28", periods=count, freq="h"),
            "absolute_error": [error] * count,
            "squared_error": [error**2] * count,
        }
    )
    summary = summarize_performance(evaluations, reference_mae=10.0)
    summary.update(model_name="taxi-test", model_version="1", run_id="run-1")
    path = tmp_path / "summary.json"
    save_performance_artifacts(evaluations, summary, tmp_path / "eval.parquet", path)
    return path, summary


# MAE tinggi saja belum cukup; batas threshold dan jumlah sample ikut menentukan status
@pytest.mark.parametrize(
    ("count", "error", "expected_status"),
    [(0, 0.0, 0), (50, 15.0, 1), (100, 12.5, 2), (100, 15.0, 3), (100, 0.0, 2)],
)
def test_evaluation_status_distinguishes_unknown_insufficient_and_degraded(
    tmp_path, count, error, expected_status
):
    path, summary = write_summary(tmp_path, count, error)
    metrics.render_metrics(path)

    assert REGISTRY.get_sample_value("taxi_model_evaluation_status") == expected_status
    assert REGISTRY.get_sample_value("taxi_model_evaluated_predictions") == count
    assert REGISTRY.get_sample_value("taxi_model_min_evaluation_samples") == 100
    assert REGISTRY.get_sample_value("taxi_model_threshold_mae") == 12.5
    assert REGISTRY.get_sample_value("taxi_model_retrain_recommended") == (
        1 if expected_status == 3 else 0
    )
    assert datetime.fromisoformat(summary["evaluated_at"]).tzinfo is not None
    mae = REGISTRY.get_sample_value("taxi_model_recent_mae")
    if count == 0:
        assert math.isnan(mae)
    else:
        assert mae == error


# summary kosong setelah promotion harus menghapus MAE dari versi sebelumnya
def test_empty_evaluation_does_not_keep_previous_mae(tmp_path):
    path, _ = write_summary(tmp_path)
    metrics.refresh_performance_metrics(path)
    assert REGISTRY.get_sample_value("taxi_model_recent_mae") == 15

    write_summary(tmp_path, count=0)
    payload, _ = metrics.render_metrics(path)

    assert b"taxi_model_recent_mae NaN" in payload
    assert REGISTRY.get_sample_value("taxi_model_evaluation_status") == 0
    assert REGISTRY.get_sample_value("taxi_model_retrain_recommended") == 0


# operational metric tetap bisa discrape ketika summary hilang atau terpotong
@pytest.mark.parametrize("replacement", [None, '{"recent_mae":'])
def test_unavailable_summary_resets_metrics_without_breaking_scrape(tmp_path, replacement):
    path, _ = write_summary(tmp_path)
    metrics.refresh_performance_metrics(path)
    if replacement is None:
        path.unlink()
    else:
        path.write_text(replacement)

    payload, content_type = metrics.render_metrics(path)

    assert b"taxi_api_requests_total" in payload
    assert content_type.startswith("text/plain")
    assert math.isnan(REGISTRY.get_sample_value("taxi_model_recent_mae"))
    assert math.isnan(REGISTRY.get_sample_value("taxi_model_last_evaluation_timestamp_seconds"))
    assert REGISTRY.get_sample_value("taxi_model_evaluation_status") == 0


# tanggal replay NYC tidak boleh ditafsirkan sebagai waktu UTC job evaluasi
def test_evaluation_and_replay_timestamps_use_their_own_clocks(tmp_path):
    path, summary = write_summary(tmp_path)
    summary.update(
        evaluated_at="2026-10-05T12:00:00+00:00",
        latest_target_datetime="2025-01-28T18:00:00",
    )
    path.write_text(json.dumps(summary))
    metrics.refresh_performance_metrics(path)

    assert REGISTRY.get_sample_value("taxi_model_last_evaluation_timestamp_seconds") == (
        datetime(2026, 10, 5, 12, tzinfo=timezone.utc).timestamp()
    )
    assert REGISTRY.get_sample_value("taxi_model_latest_target_timestamp_seconds") == (
        datetime(2025, 1, 28, 23, tzinfo=timezone.utc).timestamp()
    )


# setelah promotion hanya model dari prediction terakhir yang ditandai aktif
def test_model_switch_deactivates_previous_serving_version(tmp_path):
    metrics.MODEL_VERSION.clear()
    result = {
        "model_name": "taxi-rollout-test",
        "model_alias": "champion",
        "predicted_trip_count": 100,
    }
    for version in ("1", "2"):
        metrics.observe_prediction({**result, "model_version": version})

    samples = metrics.MODEL_VERSION.collect()[0].samples
    active = [sample.labels for sample in samples if sample.value == 1]
    assert active == [
        {"model_name": "taxi-rollout-test", "model_version": "2", "model_alias": "champion"}
    ]

    # summary punya identitas sendiri, meskipun serving sudah pindah version
    path, _ = write_summary(tmp_path)
    metrics.refresh_performance_metrics(path)
    assert REGISTRY.get_sample_value(
        "taxi_model_evaluated_version_info",
        {"model_name": "taxi-test", "model_version": "1", "run_id": "run-1"},
    ) == 1


# kalau penulisan summary baru gagal, summary lengkap sebelumnya tetap tersedia
def test_summary_replacement_failure_preserves_previous_file(tmp_path, monkeypatch):
    path, _ = write_summary(tmp_path)
    previous = path.read_text()

    def fail_replace(*args, **kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(type(path), "replace", fail_replace)
    with pytest.raises(OSError, match="replace failure"):
        write_summary(tmp_path, count=0)

    assert path.read_text() == previous
    assert not list(tmp_path.glob("*.tmp"))
