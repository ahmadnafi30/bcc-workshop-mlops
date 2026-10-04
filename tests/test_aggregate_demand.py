from datetime import date

import pandas as pd

from preprocessing.aggregate_demand import aggregate_hourly_demand


# pastikan jam tanpa pickup tetap muncul sebagai demand nol
def test_aggregate_hourly_demand_builds_complete_zone_hour_grid() -> None:
    # bikin sample trip kecil dengan dua Manhattan zone dan satu jam yang kosong
    trips = pd.DataFrame(
        {
            "tpep_pickup_datetime": pd.to_datetime(
                [
                    "2025-01-27 08:05:00",
                    "2025-01-27 08:14:00",
                    "2025-01-27 09:10:00",
                ]
            ),
            "PULocationID": [161, 161, 236],
        }
    )

    # lookup juga sengaja punya Queens supaya kita bisa cek filtering Manhattan
    zones = pd.DataFrame(
        {
            "LocationID": [161, 236, 132],
            "Borough": ["Manhattan", "Manhattan", "Queens"],
            "Zone": ["Midtown Center", "Upper East Side North", "JFK Airport"],
        }
    )

    # aggregate satu hari penuh jadi complete zone-hour grid
    result = aggregate_hourly_demand(
        trips=trips,
        zone_lookup=zones,
        target_date=date(2025, 1, 27),
    )

    # dua Manhattan zone x 24 jam harus menghasilkan 48 row
    assert len(result) == 48
    assert result["zone_id"].nunique() == 2

    # cek zone 161 jam 08:00 punya dua pickup sesuai sample
    zone_161_at_8 = result.loc[
        (result["timestamp"] == pd.Timestamp("2025-01-27 08:00:00"))
        & (result["zone_id"] == 161),
        "trip_count",
    ].item()

    # zone 236 jam 08:00 tetap harus muncul walaupun pickup-nya nol
    zone_236_at_8 = result.loc[
        (result["timestamp"] == pd.Timestamp("2025-01-27 08:00:00"))
        & (result["zone_id"] == 236),
        "trip_count",
    ].item()

    assert zone_161_at_8 == 2
    assert zone_236_at_8 == 0
