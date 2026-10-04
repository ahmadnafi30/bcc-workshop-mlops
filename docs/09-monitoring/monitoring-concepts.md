# Monitoring Concepts

Setelah model sudah bisa diserve, kita nggak cukup cuma tahu API-nya hidup.

Ada dua hal yang beda:

```text
system health
vs
model health
```

## System health

Pertanyaannya:

```text
API masih up?
request rate berapa?
latency naik nggak?
berapa request yang error?
prediction masih jalan?
```

Metric seperti ini cocok buat Prometheus.

## Model health

Pertanyaannya beda:

```text
prediction masih akurat?
MAE sekarang berapa?
lebih jelek dari waktu validation nggak?
model version mana yang performanya turun?
```

Model metric baru bisa dihitung setelah ground truth datang.

Jadi lifecycle-nya:

```text
target hour
    ↓
prediction dibuat
    ↓
prediction dicatat

beberapa waktu kemudian
    ↓
actual demand tersedia
    ↓
prediction vs actual
    ↓
MAE / RMSE
```

## Kenapa prediction harus dilog?

Kalau kita cuma expose metric prediction count, kita nggak punya pasangan:

```text
prediction
actual
```

Makanya setiap successful prediction masuk append-only file:

```text
data/monitoring/predictions.jsonl
```

Isi pentingnya:

```text
target_datetime
zone_id
predicted_trip_count
model_version
run_id
logged_at
```

Begitu processed demand untuk target hour tersedia, evaluation job bisa nyari actual value.

## Reference performance

Kita nggak pakai threshold MAE random.

Reference diambil dari validation MAE champion model di MLflow.

Misalnya:

```text
champion validation MAE = 10
```

dan multiplier:

```text
1.25
```

maka threshold:

```text
10 x 1.25 = 12.5
```

Kalau recent MAE di atas 12.5 dan sample sudah cukup, monitoring kasih:

```text
retrain_recommended = true
```

Multiplier dan minimum sample tetap configurable karena tolerance production tiap use case bisa beda.

## Monitoring bukan retraining

Monitoring cuma jawab:

> performa turun nggak?

Retraining jawab:

> kalau turun, kita ngapain?

Keduanya sengaja dipisah supaya sistem nggak retrain cuma gara-gara satu request error besar.
