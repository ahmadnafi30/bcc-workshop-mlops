from datetime import date

import pandas as pd


# cek kolom minimum sebelum trip kita ubah jadi hourly demand
def validate_trip_columns(trips: pd.DataFrame) -> None:
    # tentuin schema minimum yang wajib ada di daily trip batch
    required_columns = {"tpep_pickup_datetime", "PULocationID"}
    missing_columns = required_columns.difference(trips.columns)

    # gagal lebih awal kalau input batch ternyata schema-nya nggak sesuai
    if missing_columns:
        raise ValueError(
            "trip data kehilangan kolom: " + ", ".join(sorted(missing_columns))
        )


# ambil id dan nama zone manhattan buat bikin grid demand yang lengkap
def get_manhattan_zone_table(zone_lookup: pd.DataFrame) -> pd.DataFrame:
    # cek dulu lookup punya kolom yang kita butuhin buat filter dan naming zone
    required_columns = {"LocationID", "Borough", "Zone"}
    missing_columns = required_columns.difference(zone_lookup.columns)

    if missing_columns:
        raise ValueError(
            "taxi zone lookup kehilangan kolom: "
            + ", ".join(sorted(missing_columns))
        )

    # pilih zone Manhattan aja karena itu scope forecasting kita
    zones = zone_lookup.loc[
        zone_lookup["Borough"].astype(str).str.casefold().eq("manhattan"),
        ["LocationID", "Zone"],
    ].copy()

    # samain tipe id biar nanti cocok sama PULocationID dari trip data
    zones["LocationID"] = pd.to_numeric(
        zones["LocationID"],
        errors="raise",
    ).astype("int16")

    # satu location id cukup muncul sekali di zone table
    return zones.drop_duplicates("LocationID").sort_values("LocationID")


# ubah trip-level data jadi satu row per zone per jam dan isi demand kosong nol
def aggregate_hourly_demand(
    trips: pd.DataFrame,
    zone_lookup: pd.DataFrame,
    target_date: date,
) -> pd.DataFrame:
    # validasi input lalu siapin master list zone Manhattan
    validate_trip_columns(trips)
    zones = get_manhattan_zone_table(zone_lookup)

    # copy dua kolom yang dibutuhin lalu rapihin tipe datanya
    working = trips[["tpep_pickup_datetime", "PULocationID"]].copy()
    working["tpep_pickup_datetime"] = pd.to_datetime(
        working["tpep_pickup_datetime"],
        errors="coerce",
    )
    working["PULocationID"] = pd.to_numeric(
        working["PULocationID"],
        errors="coerce",
    )

    # bikin batas satu hari penuh sesuai batch yang lagi diproses
    day_start = pd.Timestamp(target_date)
    day_end = day_start + pd.Timedelta(days=1)

    # keep cuma trip pada tanggal target dan pickup zone yang masuk Manhattan
    working = working.loc[
        working["tpep_pickup_datetime"].between(
            day_start,
            day_end,
            inclusive="left",
        )
        & working["PULocationID"].isin(zones["LocationID"])
    ].dropna()

    # bulatin pickup time ke jam lalu samain nama zone id buat dataset demand
    working["timestamp"] = working["tpep_pickup_datetime"].dt.floor("h")
    working["zone_id"] = working["PULocationID"].astype("int16")

    # hitung berapa pickup yang terjadi untuk setiap kombinasi jam dan zone
    counts = (
        working.groupby(["timestamp", "zone_id"], observed=True)
        .size()
        .rename("trip_count")
    )

    # bikin semua kombinasi 24 jam x seluruh zone supaya time series-nya lengkap
    hours = pd.date_range(day_start, periods=24, freq="h")
    full_index = pd.MultiIndex.from_product(
        [hours, zones["LocationID"].tolist()],
        names=["timestamp", "zone_id"],
    )

    # kombinasi yang nggak punya pickup tetap disimpan dengan trip_count nol
    demand = counts.reindex(full_index, fill_value=0).reset_index()
    demand["trip_count"] = demand["trip_count"].astype("int32")

    # tambahin human-readable zone name biar hasilnya enak dilihat waktu workshop
    zone_names = zones.rename(
        columns={"LocationID": "zone_id", "Zone": "zone"}
    )
    demand = demand.merge(zone_names, on="zone_id", how="left")

    # balikin kolom final dalam urutan yang konsisten
    return demand[
        ["timestamp", "zone_id", "zone", "trip_count"]
    ].sort_values(["timestamp", "zone_id"]).reset_index(drop=True)
