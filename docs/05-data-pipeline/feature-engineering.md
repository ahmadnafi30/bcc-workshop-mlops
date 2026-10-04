# Feature Engineering

Setelah hourly demand siap, next step-nya adalah bikin dataset yang benar-benar bisa dipakai model.

Input kita masih seperti ini:

```text
timestamp            zone_id    trip_count
2025-01-08 17:00     161        169
2025-01-08 18:00     161        182
...
```

Model belum cukup dikasih `trip_count` mentah. Kita perlu kasih context dari waktu sebelumnya.

## Siapin history awal

Sebelum production replay mulai tanggal 27 January, kita siapin dulu history untuk initial training dan validation:

```bash
uv run python scripts/prepare_historical_demand.py
```

Default range-nya:

```text
2025-01-01 sampai 2025-01-26
```

Script ini langsung baca replay source hasil bootstrap lalu bikin:

```text
data/processed/demand/2025-01-01.parquet
data/processed/demand/2025-01-02.parquet
...
data/processed/demand/2025-01-26.parquet
```

Ini beda sama production replay. Initial history memang sudah kita anggap available buat bikin model pertama.

## Build features

Setelah processed demand lengkap:

```bash
uv run python scripts/build_features.py
```

Output:

```text
data/features/taxi_demand_features.parquet
```

Feature yang kita bikin:

```text
zone_id
hour
day_of_week
is_weekend

lag_1h
lag_2h
lag_3h
lag_24h
lag_168h

rolling_mean_3h
rolling_mean_6h
rolling_mean_24h

target_trip_count
```

## Kenapa ada warm-up period?

Kita punya `lag_168h`, artinya model butuh history satu minggu.

Jadi data 1-7 January tetap penting, tapi belum langsung jadi row training yang lengkap. Data itu dipakai sebagai context buat row setelahnya.

Kurang lebih:

```text
Jan 01 - Jan 07
warm-up history

Jan 08 - Jan 21
effective training rows

Jan 22 - Jan 26
validation

Jan 27 onward
production replay
```

Ini lebih natural dibanding maksa row awal tetap dipakai padahal history satu minggunya belum ada.

## Avoiding leakage

Bagian yang paling penting bukan sekadar bikin lag, tapi jangan sampai model ngelihat future.

Misalnya kita mau prediksi demand jam 18:00.

```text
lag_1h  -> demand 17:00
lag_2h  -> demand 16:00
lag_24h -> demand kemarin jam 18:00
```

Rolling mean 3 jam juga harus:

```text
mean(
  demand 15:00,
  demand 16:00,
  demand 17:00
)
```

bukan ikut memasukkan demand 18:00.

Makanya di code, rolling feature di-`shift(1)` dulu sebelum dihitung.

## Kenapa file feature digabung jadi satu?

Processed demand sengaja disimpan per hari karena itu cocok buat batch pipeline.

Untuk training, lebih enak kalau history yang sudah siap digabung jadi satu model-ready dataset:

```text
daily processed demand
        ↓
combine date range
        ↓
feature engineering
        ↓
taxi_demand_features.parquet
```

Setelah feature dataset siap, kita freeze data yang dipakai training menjadi **training snapshot** dan versioning-nya ditangani DVC.

```bash
uv run dvc repro create_training_snapshot
```

Output initial snapshot:

```text
data/snapshots/training/taxi_demand_2025-01-26.parquet
```

Jadi feature dataset boleh berkembang, tapi input model initial tetap punya version yang jelas. Detailnya ada di [DVC and Training Snapshots](../03-tools/dvc.md).
