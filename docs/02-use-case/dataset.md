# Dataset

Dataset utama yang kita pakai adalah **NYC TLC Yellow Taxi Trip Records**. Dari dataset ini kita sudah punya informasi waktu dan lokasi pickup yang cukup buat ngebangun taxi demand forecasting dari awal sampai production.

Kalau mau bikin feature-nya lebih kaya, dataset ini juga bisa dikombinasikan dengan weather data, misalnya temperature, rainfall, snowfall, atau wind speed. Bagian weather sifatnya optional, jadi core pipeline tetap bisa jalan hanya dengan TLC data.

## Main source

Official source:

`https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page`

Kita pakai periode:

```text
yellow_tripdata_2025-01.parquet
yellow_tripdata_2025-02.parquet
yellow_tripdata_2025-03.parquet
```

Kita juga pakai **Taxi Zone Lookup** dari TLC yang sama untuk mapping:

```text
LocationID -> Borough -> Zone
```

Jadi secara project, ini tetap satu source ecosystem.

## What does one raw row mean?

Satu row pada raw Yellow Taxi dataset adalah **satu taxi trip**.

Simplified example:

| pickup_datetime | dropoff_datetime | PULocationID | DOLocationID | passenger_count | trip_distance | fare_amount |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2025-01-15 17:04 | 2025-01-15 17:19 | 161 | 236 | 1 | 2.4 | 17.5 |
| 2025-01-15 17:08 | 2025-01-15 17:31 | 161 | 230 | 2 | 3.1 | 21.0 |
| 2025-01-15 17:12 | 2025-01-15 17:26 | 236 | 162 | 1 | 1.8 | 14.2 |

Raw dataset punya lebih banyak column daripada yang kita butuhkan.

## Columns we actually need

Untuk demand forecasting, core fields yang paling penting justru sedikit:

| Column | Dipakai buat |
| --- | --- |
| `tpep_pickup_datetime` | menentukan tanggal dan jam pickup |
| `PULocationID` | menentukan pickup zone |

Dari Taxi Zone Lookup:

| Column | Dipakai buat |
| --- | --- |
| `LocationID` | join key |
| `Borough` | filter Manhattan |
| `Zone` | human-readable zone name |

Field seperti `fare_amount`, `tip_amount`, `trip_distance`, atau `passenger_count` tetap interesting buat analytics, tapi bukan core feature untuk memprediksi demand satu jam ke depan.

Sebagian informasi trip pada target hour bahkan belum available ketika prediction dibuat. Kalau future information itu ikut dipakai, kita bisa kena **data leakage**.

## From trip-level to demand-level

Raw data:

```text
17:04 -> pickup zone 161
17:08 -> pickup zone 161
17:12 -> pickup zone 236
17:17 -> pickup zone 161
17:24 -> pickup zone 236
...
```

Setelah aggregation:

```text
timestamp            zone_id    trip_count
2025-01-15 17:00     161        176
2025-01-15 17:00     236        143
2025-01-15 18:00     161        191
2025-01-15 18:00     236        151
```

`trip_count` inilah yang kita anggap sebagai **taxi demand**.

Granularity berubah dari:

```text
1 row = 1 trip
```

menjadi:

```text
1 row = 1 zone x 1 hour
```

Selain lebih cocok untuk forecasting, hasil aggregation ini juga jauh lebih ringan untuk training dibanding jutaan raw trip.

## Manhattan filtering

Flow-nya:

```text
PULocationID
    ↓
Taxi Zone Lookup
    ↓
Borough
    ↓
keep only Borough == Manhattan
```

Kita fokus ke pickup zone, bukan dropoff zone. Jadi kalau pickup terjadi di Manhattan lalu dropoff di Queens, record itu tetap termasuk.

## Data period and split

| Period | Role |
| --- | --- |
| Jan 1 - Jan 7 | warm-up history |
| Jan 8 - Jan 21 | initial training |
| Jan 22 - Jan 26 | validation |
| Jan 27 onward | simulated production |

Kita pakai time-based split, bukan random split, karena model di dunia nyata selalu memprediksi future berdasarkan past.

## Data flow inside the project

Secara konsep nanti:

```text
TLC monthly parquet
        ↓
bootstrap process
        ↓
historical replay source
        ↓
simulate one production day
        ↓
data/raw/trips/YYYY-MM-DD.parquet
        ↓
preprocessing
        ↓
data/processed/
        ↓
feature engineering
        ↓
data/features/
```

Training snapshot yang benar-benar dipakai model nanti disimpan terpisah dan di-version menggunakan DVC.

## Optional: combine with weather data

Kalau mau bikin use case-nya sedikit lebih interesting, kita bisa tambahin weather data sebagai external feature.

Contohnya:

```text
temperature
rainfall
snowfall
wind_speed
```

Nanti weather data tinggal di-join berdasarkan waktu:

```text
Taxi Data ─────┐
               ├── Feature Engineering
Weather Data ──┘
```

Secara use case ini cukup masuk akal karena kondisi cuaca bisa ikut memengaruhi mobility demand. Tapi weather bukan requirement utama project, jadi kalau bagian ini mau di-skip, seluruh MLOps pipeline tetap bisa jalan seperti biasa.