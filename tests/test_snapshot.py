from pathlib import Path

import pandas as pd

from data_versioning.snapshot import (
    build_snapshot_name,
    calculate_file_sha256,
    create_training_snapshot,
)


# pastikan cutoff date nggak pernah masukin row dari future
def test_create_training_snapshot_respects_cutoff_date() -> None:
    # sample punya satu row setelah cutoff supaya filtering gampang dicek
    features = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2025-01-25 23:00:00",
                    "2025-01-26 23:00:00",
                    "2025-01-27 00:00:00",
                ]
            ),
            "zone_id": [161, 161, 161],
            "target_trip_count": [10, 20, 30],
        }
    )

    snapshot = create_training_snapshot(
        features=features,
        cutoff_date="2025-01-26",
    )

    assert len(snapshot) == 2
    assert snapshot["target_trip_count"].tolist() == [10, 20]


# pastikan nama snapshot konsisten dan gampang ditebak dari cutoff date
def test_build_snapshot_name() -> None:
    assert (
        build_snapshot_name("2025-01-26")
        == "taxi_demand_2025-01-26.parquet"
    )


# pastikan fingerprint berubah kalau isi file berubah
def test_calculate_file_sha256_detects_file_change(tmp_path: Path) -> None:
    # dua isi berbeda harus menghasilkan fingerprint berbeda
    path = tmp_path / "sample.txt"
    path.write_text("version-one", encoding="utf-8")
    first = calculate_file_sha256(path)

    path.write_text("version-two", encoding="utf-8")
    second = calculate_file_sha256(path)

    assert first != second
