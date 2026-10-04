# Airflow

Airflow di project ini bukan tempat kita nulis ulang business logic.

Business logic tetap ada di `src/`. Airflow tugasnya ngatur:

```text
kapan task jalan
        +
urutan task
        +
dependency antar task
        +
status setiap run
```

Jadi cara bacanya:

```text
src/
"how"

dags/
"when + in what order"
```

## Kenapa pakai TaskFlow?

DAG workshop ini pakai TaskFlow API dari Airflow 3:

```python
from airflow.sdk import dag, task
```

TaskFlow bikin DAG lebih dekat ke Python biasa. Return value kecil dari satu task bisa diteruskan ke task berikutnya sebagai XCom.

Di project ini XCom cuma dipakai buat metadata kecil:

```text
date
rows
zones
path
metric
run_id
```

Kita **nggak** masukin DataFrame atau file parquet ke XCom.

Data besar tetap lewat filesystem:

```text
data/raw/
data/processed/
data/features/
data/snapshots/
```

## Install

Airflow ada di dependency group terpisah:

```bash
uv sync --group airflow
```

Project pin:

```text
apache-airflow==3.3.2
```

## Start local Airflow

Jalankan:

```bash
uv run --group airflow python scripts/start_airflow.py
```

Script ini otomatis set:

```text
AIRFLOW_HOME=<project>/.airflow
AIRFLOW__CORE__DAGS_FOLDER=<project>/dags
```

lalu menjalankan:

```text
airflow standalone
```

Setelah startup selesai, Airflow UI biasanya tersedia di:

```text
http://localhost:8080
```

Credential local akan muncul di terminal saat standalone pertama kali dijalankan.

## DAG yang kita punya

### taxi_daily_replay

DAG ini merepresentasikan satu production day.

```text
replay date
    ↓
release batch
    ↓
validate
    ↓
aggregate demand
    ↓
rebuild features
```

Trigger-nya manual supaya pas workshop kita bisa pilih tanggal:

```text
2025-01-27
2025-01-28
2025-01-29
...
```

### taxi_initial_training

DAG ini ngurus lifecycle candidate model:

```text
DVC reproduce snapshot
        ↓
MLflow training
        ↓
baseline comparison
        ↓
beat baseline?
   /            \
 no             yes
 ↓               ↓
stop       register challenger
```

Model **nggak** otomatis dipromote ke `champion`.

Promotion tetap explicit:

```bash
uv run python scripts/promote_model.py --version <VERSION>
```

### taxi_model_monitoring

DAG ini evaluate champion model dari prediction log yang actual demand-nya sudah tersedia.

```text
evaluate champion
      ↓
recent MAE > threshold?
   /              \
 no               yes
 ↓                 ↓
stop          new snapshot
                   ↓
                retrain
                   ↓
             challenger
```

Champion tetap nggak auto-promote.

## Kenapa beberapa DAG?

Kalau semuanya dimasukin satu DAG, kita jadi seolah-olah harus retrain model setiap ada daily batch.

Padahal production flow yang lebih masuk akal:

```text
daily data pipeline
jalan sering

model training pipeline
jalan saat memang dibutuhkan
```

Monitoring sekarang yang menentukan kapan retraining memang perlu dijalankan.
