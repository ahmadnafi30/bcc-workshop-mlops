from orchestration.monitoring_pipeline import retrain_if_recommended


# pastikan healthy model berhenti sebelum snapshot atau training dijalankan
def test_retrain_if_recommended_skips_healthy_model(tmp_path) -> None:
    result = retrain_if_recommended(
        project_root=tmp_path,
        monitoring_result={
            "retrain_recommended": False,
            "latest_target_datetime": "2025-01-28T23:00:00",
        },
    )

    assert result["status"] == "not_needed"
    assert result["reason"] == "performance_within_threshold"
