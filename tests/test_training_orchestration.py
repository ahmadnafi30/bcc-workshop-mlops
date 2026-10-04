from orchestration.training_pipeline import register_challenger


# pastikan candidate yang kalah dari baseline nggak otomatis masuk registry
def test_register_challenger_skips_worse_model() -> None:
    # function harus stop sebelum nyentuh MLflow server kalau gate-nya gagal
    result = register_challenger(
        {
            "model_beats_baseline": False,
            "model_run_id": "run-123",
        }
    )

    assert result["status"] == "not_registered"
    assert result["run_id"] == "run-123"
