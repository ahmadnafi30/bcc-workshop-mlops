import pandas as pd

from monitoring.performance import (
    build_evaluation_table,
    summarize_performance,
)


# pastikan prediction baru bisa dievaluate setelah processed ground truth tersedia
def test_build_evaluation_table_matches_ground_truth(tmp_path) -> None:
    demand_dir = tmp_path / "demand"
    demand_dir.mkdir()

    pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2025-01-28 18:00:00"]),
            "zone_id": [161],
            "trip_count": [100],
        }
    ).to_parquet(
        demand_dir / "2025-01-28.parquet",
        index=False,
    )

    records = [
        {
            "logged_at": "2025-01-28T18:01:00+00:00",
            "target_datetime": "2025-01-28T18:00:00",
            "zone_id": 161,
            "predicted_trip_count": 112.0,
            "model_name": "taxi-model",
            "model_version": "2",
            "model_alias": "champion",
            "run_id": "run-2",
        }
    ]

    result = build_evaluation_table(
        prediction_records=records,
        demand_dir=demand_dir,
        model_version="2",
    )

    assert len(result) == 1
    assert result.iloc[0]["actual_trip_count"] == 100
    assert result.iloc[0]["absolute_error"] == 12


# pastikan retraining baru direkomendasikan kalau sample cukup dan recent mae melewati threshold
def test_summarize_performance_uses_reference_threshold() -> None:
    evaluations = pd.DataFrame(
        {
            "target_datetime": pd.date_range(
                "2025-01-28",
                periods=120,
                freq="h",
            ),
            "absolute_error": [15.0] * 120,
            "squared_error": [225.0] * 120,
        }
    )

    summary = summarize_performance(
        evaluations=evaluations,
        reference_mae=10.0,
        degradation_multiplier=1.25,
        min_samples=100,
        recent_limit=500,
    )

    assert summary["evaluation_count"] == 120
    assert summary["recent_mae"] == 15.0
    assert summary["threshold_mae"] == 12.5
    assert summary["retrain_recommended"] is True
