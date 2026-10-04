# Baseline Training

Sebelum masuk MLflow, kita bikin training flow yang bisa jalan manual dulu.

Goal-nya simple: jangan sampai kita install experiment tracking tapi belum punya experiment yang meaningful buat dibandingin.

## Dua model yang dibandingin

Kita mulai dari dua approach.

Pertama, **naive 24h baseline**:

```text
prediction(t) = demand(t - 24h)
```

Kalau mau prediksi demand Selasa jam 18:00, baseline cukup pakai demand Senin jam 18:00.

Kedua, **HistGradientBoostingRegressor** dari scikit-learn.

Model ini pakai semua feature yang sudah kita bikin:

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
```

`zone_id` diperlakukan sebagai categorical feature. Jadi model nggak menganggap zone 200 secara arti "lebih besar" daripada zone 100.

## Run training

Pastikan sebelumnya sudah jalan:

```bash
uv run python scripts/bootstrap_data.py
uv run python scripts/prepare_historical_demand.py
uv run python scripts/build_features.py
uv run dvc repro create_training_snapshot
```

Training sekarang baca snapshot DVC, bukan langsung dari feature file yang bisa terus berubah.

Lalu train:

```bash
uv run python scripts/train_model.py
```

Output terminal kurang lebih:

```text
validation result
naive 24h              -> MAE ...
hist gradient boosting -> MAE ...
model beats baseline  -> True
```

Exact angkanya baru kita percaya setelah beneran run ke data TLC yang sudah didownload.

## Time-based split

Kita tetap nggak pakai random split.

```text
Jan 01 - Jan 07
warm-up history

Jan 08 - Jan 21
training

Jan 22 - Jan 26
validation
```

Jadi validation benar-benar datang setelah training period.

## Artifact sementara

Untuk sekarang model disimpan ke:

```text
models/taxi_demand_model.joblib
```

Metric awal disimpan ke:

```text
models/initial_metrics.json
```

Ini masih cara manual.

Nanti saat MLflow masuk, problem yang mau kita selesaikan jadi jelas:

```text
run 1
baseline

run 2
gradient boosting config A

run 3
gradient boosting config B

run 4
model baru setelah retraining
```

Kalau semua metric, parameter, dan artifact disimpan manual pakai file, lama-lama susah dilacak. Di situlah MLflow mulai kepake.

## Kenapa baseline tetap disimpan?

Karena "model jalan" belum tentu berarti "model bagus".

Kalau gradient boosting ternyata punya MAE lebih jelek daripada rule kemarin-jam-yang-sama, berarti complexity tambahan belum kasih value.

Jadi comparison yang kita cari bukan:

```text
model A vs model B doang
```

tapi juga:

```text
ML model vs simple baseline
```

Ini nanti bikin experiment tracking kita lebih meaningful.
