from datetime import date

import pandas as pd
import pytest

from ingestion.replay import validate_daily_batch


# pastikan valid batch lolos dan summary yang dibalikin tetap kecil
def test_validate_daily_batch_accepts_matching_date(tmp_path) -> None:
    # sample CSV cukup dua trip pada tanggal yang sama
    path = tmp_path / "2025-01-27.csv"
    pd.DataFrame(
        {
            "tpep_pickup_datetime": pd.to_datetime(
                [
                    "2025-01-27 08:00:00",
                    "2025-01-27 09:00:00",
                ]
            ),
            "PULocationID": [161, 162],
        }
    ).to_csv(path, index=False)

    result = validate_daily_batch(
        batch_path=path,
        target_date=date(2025, 1, 27),
    )

    assert result["status"] == "valid"
    assert result["rows"] == 2
    assert result["zones"] == 2


# pastikan timestamp dari tanggal lain langsung bikin validation gagal
def test_validate_daily_batch_rejects_wrong_date(tmp_path) -> None:
    # row kedua sengaja masuk tanggal berikutnya buat simulasi batch bocor
    path = tmp_path / "2025-01-27.csv"
    pd.DataFrame(
        {
            "tpep_pickup_datetime": pd.to_datetime(
                [
                    "2025-01-27 23:00:00",
                    "2025-01-28 00:00:00",
                ]
            ),
            "PULocationID": [161, 162],
        }
    ).to_csv(path, index=False)

    with pytest.raises(ValueError, match="tanggal di luar"):
        validate_daily_batch(
            batch_path=path,
            target_date=date(2025, 1, 27),
        )
