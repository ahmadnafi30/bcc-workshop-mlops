# Retraining

Retraining di project ini bukan cron job yang asal train ulang tiap malam.

Trigger-nya datang dari model performance.

## Decision flow

```text
prediction log
      ↓
ground truth available
      ↓
recent MAE
      ↓
compare champion validation MAE
      ↓
degraded?
   /        \
 no         yes
 ↓           ↓
stop      retrain
             ↓
         challenger
```

Default threshold:

```text
recent_mae > reference_mae x 1.25
```

dan minimum:

```text
100 evaluated predictions
```

Keduanya bisa diubah dari Airflow trigger params.

## Kenapa perlu minimum sample?

Satu prediction bisa error besar karena kondisi lokal yang aneh.

Kita nggak mau sistem langsung retrain cuma karena satu titik.

Minimum sample bikin decision lihat pattern, bukan satu outlier.

## Snapshot retraining

Kalau monitoring recommend retraining, cutoff snapshot diambil dari actual target paling baru yang sudah dievaluate.

Contoh:

```text
latest evaluated target
2025-02-10 23:00

snapshot
taxi_demand_2025-02-10.parquet
```

Snapshot tetap punya SHA256 dan metadata yang ikut dicatat ke MLflow.

## Validation window ikut maju

Initial model:

```text
Jan 08 - Jan 21
train

Jan 22 - Jan 26
validation
```

Retraining snapshot sampai Feb 10:

```text
history sampai Feb 05
train

Feb 06 - Feb 10
validation
```

Jadi validation selalu lima hari paling akhir dari snapshot, bukan tanggal hard-coded.

## Auto retrain bukan auto promote

Setelah retraining:

```text
new model
   ↓
beat naive baseline?
   ↓ yes
register challenger
```

Tapi alias:

```text
champion
```

nggak berubah otomatis.

Kita masih review candidate dulu sebelum:

```bash
uv run python scripts/promote_model.py --version <VERSION>
```

Boundary ini penting.

Automation boleh bantu bikin candidate baru, tapi decision production masih explicit di workshop ini.

## Run dari Airflow

Trigger:

```text
taxi_model_monitoring
```

Parameter default:

```text
degradation_multiplier = 1.25
min_samples             = 100
recent_limit            = 500
```

Kalau belum cukup ground truth, DAG selesai tanpa retraining.

Kalau metric masih sehat, DAG juga selesai tanpa retraining.

Training baru benar-benar jalan ketika monitoring condition terpenuhi.
