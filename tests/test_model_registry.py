from tracking.model_registry import build_registered_model_uri


# pastikan serving uri pakai alias dan nggak bergantung ke hard-coded version
def test_build_registered_model_uri_uses_alias() -> None:
    # custom model name bikin test ini nggak tergantung environment variable lokal
    uri = build_registered_model_uri(
        alias="champion",
        model_name="taxi-model-test",
    )

    assert uri == "models:/taxi-model-test@champion"
