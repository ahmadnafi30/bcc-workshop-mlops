# Feature and Model Design

Setelah raw trip di-aggregate, dataset ML kita berubah menjadi hourly demand per zone.

Hal paling penting di bagian ini adalah memastikan semua feature yang dipakai memang **available sebelum target hour terjadi**.

## Row definition

Anggap satu row punya target hour `t`.

Contohnya:

```text
zone_id = 161
target_hour = 2025-01-15 18:00
```

Target-nya adalah jumlah pickup selama 18:00-18:59.

Feature historis hanya boleh menggunakan informasi sampai sebelum 18:00.

```text
lag_1h  = demand 17:00
lag_2h  = demand 16:00
lag_3h  = demand 15:00
lag_24h = demand yesterday at 18:00
```

## Target

Target utama:

```text
target_trip_count
```

Definisinya: jumlah Yellow Taxi pickup pada suatu Manhattan taxi zone selama target hour.

Secara sederhana:

```text
y(zone, t) = number of pickups in zone during hour t
```

## Feature set

### Calendar features

```text
zone_id
hour
day_of_week
is_weekend
```

Calendar feature berguna karena demand taxi punya pattern berdasarkan waktu.

```text
08:00 weekday != 08:00 Sunday
18:00 Friday  != 18:00 Monday
```

### Lag features

```text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
```

| Feature | Meaning |
| --- | --- |
| `lag_1h` | demand satu jam sebelumnya |
| `lag_2h` | demand dua jam sebelumnya |
| `lag_3h` | demand tiga jam sebelumnya |
| `lag_24h` | demand pada jam yang sama kemarin |
| `lag_168h` | demand pada jam yang sama minggu lalu |

`lag_168h` bikin beberapa hari awal dataset belum punya feature lengkap. Itu normal dan nanti kita handle saat preprocessing.

### Rolling features

```text
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
```

Rolling window harus dihitung dari historical values sebelum target hour, bukan termasuk target itu sendiri.

Untuk target 18:00:

```text
rolling_mean_3h
=
mean(demand 15:00, demand 16:00, demand 17:00)
```

## Example ML row

```text
target_hour          2025-01-15 18:00
zone_id              161

hour                  18
day_of_week            2
is_weekend             0

lag_1h               169
lag_2h               153
lag_3h               141
lag_24h              162
lag_168h             174

rolling_mean_3h      154.3
rolling_mean_6h      146.8
rolling_mean_24h     121.6

target_trip_count     182
```

## Baseline first

Sebelum pakai ML model, kita butuh simple baseline.

```text
prediction(t) = demand(t - 24h)
```

Artinya demand jam 18:00 hari ini diprediksi sama dengan demand jam 18:00 kemarin.

Baseline penting karena model ML yang lebih kompleks tetap harus menjawab satu pertanyaan sederhana:

> Apakah model kita beneran lebih bagus dibanding rule sederhana?

Nanti baseline juga kita log ke MLflow.

## Main model

Untuk core workshop, pilihan utama kita adalah **HistGradientBoostingRegressor** dari scikit-learn.

Alasannya:

- training relatif cepat,
- bisa menangkap nonlinear pattern,
- tidak butuh GPU,
- dependency tetap ringan,
- peserta bisa fokus ke MLOps, bukan model tuning.

Random Forest bisa jadi additional experiment kalau waktunya cukup.

Kita sengaja belum pakai LSTM atau Transformer. Model forecasting yang lebih complex bisa jadi extension, tapi bukan inti workshop.

## Evaluation metrics

### Primary metric: MAE

Kalau `MAE = 10`, artinya secara rata-rata prediction meleset sekitar 10 pickup per zone-hour.

MAE gampang dijelaskan dan intuitive buat workshop.

### Secondary metric: RMSE

RMSE ikut kita log untuk melihat apakah ada error besar yang cukup ekstrem.

Jadi minimal MLflow akan mencatat:

```text
mae
rmse
```

## Time-based split

```text
Jan 01 ───────── Jan 21
      TRAIN

Jan 22 ─ Jan 26
   VALIDATION

Jan 27 ───────────── Mar 31
      PRODUCTION REPLAY
```

Kita tidak pakai random split karena model seharusnya belajar dari past dan dievaluate ke future.

## Retraining idea

Setelah masuk simulated production, kita collect recent prediction dan actual demand.

Rule awal bisa sesederhana:

```python
if recent_mae > threshold:
    retrain = True
```

Tapi model tidak akan diretrain setiap kali ada batch baru.

Goal-nya justru menunjukkan bahwa retraining adalah **decision**, bukan ritual yang dijalankan tanpa alasan.