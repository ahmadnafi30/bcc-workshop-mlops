import pytest

from ingestion.taxi import build_trip_url, validate_month


# pastikan url yellow taxi kebentuk konsisten dari bulan yang valid
def test_build_trip_url_uses_official_month_pattern() -> None:
    # bikin satu url sample lalu cek naming pattern file official-nya
    url = build_trip_url("2025-01")

    assert url.endswith("/yellow_tripdata_2025-01.parquet")


# pastikan format bulan aneh gagal lebih awal sebelum proses download jalan
@pytest.mark.parametrize("month", ["2025-1", "25-01", "2025-13", "january"])
def test_validate_month_rejects_invalid_format(month: str) -> None:
    # seluruh input invalid ini harus berhenti di validation, bukan lanjut ke download
    with pytest.raises(ValueError):
        validate_month(month)
