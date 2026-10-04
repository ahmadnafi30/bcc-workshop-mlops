from datetime import date

import pandas as pd


def validate_trip_columns(trips: pd.DataFrame) -> None:
    """cek kolom minimum sebelum trip kita ubah jadi hourly demand."""
    required_columns = {"tpep_pickup_datetime", "PULocationID"}
    missing_columns = required_columns.difference(trips.columns)

    if missing_columns:
        raise ValueError(
            "trip data kehilangan kolom: " + ", ".join(sorted(missing_columns))
        )


def get_manhattan_zone_table(zone_lookup: pd.DataFrame) -> pd.DataFrame:
    """ambil id dan nama zone manhattan buat bikin grid demand yang lengkap."""
    required_columns = {"LocationID", "Borough", "Zone"}
    missing_columns = required_columns.difference(zone_lookup.columns)

    if missing_columns:
        raise ValueError(
            "taxi zone lookup kehilangan kolom: "
            + ", ".join(sorted(missing_columns))
        )

    zones = zone_lookup.loc[
        zone_lookup["Borough"].astype(str).str.casefold().eq("manhattan"),
        ["LocationID", "Zone"],
    ].copy()

    zones["LocationID"] = pd.to_numeric(
        zones["LocationID"],
        errors="raise",
    ).astype("int16")

    return zones.drop_duplicates("LocationID").sort_values("LocationID")


def aggregate_hourly_demand(
    trips: pd.DataFrame,
    zone_lookup: pd.DataFrame,
    target_date: date,
) -> pd.DataFrame:
    """ubah trip-level data jadi satu row per zone per jam dan isi demand kosong nol."""
    validate_trip_columns(trips)
    zones = get_manhattan_zone_table(zone_lookup)

    working = trips[["tpep_pickup_datetime", "PULocationID"]].copy()
    working["tpep_pickup_datetime"] = pd.to_datetime(
        working["tpep_pickup_datetime"],
        errors="coerce",
    )
    working["PULocationID"] = pd.to_numeric(
        working["PULocationID"],
        errors="coerce",
    )

    day_start = pd.Timestamp(target_date)
    day_end = day_start + pd.Timedelta(days=1)

    working = working.loc[
        working["tpep_pickup_datetime"].between(
            day_start,
            day_end,
            inclusive="left",
        )
        & working["PULocationID"].isin(zones["LocationID"])
    ].dropna()

    working["timestamp"] = working["tpep_pickup_datetime"].dt.floor("h")
    working["zone_id"] = working["PULocationID"].astype("int16")

    counts = (
        working.groupby(["timestamp", "zone_id"], observed=True)
        .size()
        .rename("trip_count")
    )

    hours = pd.date_range(day_start, periods=24, freq="h")
    full_index = pd.MultiIndex.from_product(
        [hours, zones["LocationID"].tolist()],
        names=["timestamp", "zone_id"],
    )

    demand = counts.reindex(full_index, fill_value=0).reset_index()
    demand["trip_count"] = demand["trip_count"].astype("int32")

    zone_names = zones.rename(
        columns={"LocationID": "zone_id", "Zone": "zone"}
    )
    demand = demand.merge(zone_names, on="zone_id", how="left")

    return demand[
        ["timestamp", "zone_id", "zone", "trip_count"]
    ].sort_values(["timestamp", "zone_id"]).reset_index(drop=True)
