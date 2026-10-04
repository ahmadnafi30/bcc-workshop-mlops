import pytest

from ingestion.taxi import build_trip_url, validate_month


def test_build_trip_url_uses_official_month_pattern() -> None:
    """pastikan url yellow taxi kebentuk konsisten dari bulan yang valid."""
    url = build_trip_url("2025-01")

    assert url.endswith("/yellow_tripdata_2025-01.parquet")


@pytest.mark.parametrize("month", ["2025-1", "25-01", "2025-13", "january"])
def test_validate_month_rejects_invalid_format(month: str) -> None:
    """pastikan format bulan aneh gagal lebih awal sebelum proses download jalan."""
    with pytest.raises(ValueError):
        validate_month(month)
