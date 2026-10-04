# Airflow Orchestration

Sebelum Airflow masuk, semua step ini sebenarnya sudah bisa dijalankan manual.

Itu sengaja.

Airflow baru masuk setelah setiap business logic punya function yang jelas. Jadi DAG kita nggak berisi ratusan baris preprocessing atau training code.

## Preparation

Pertama install Airflow group:

```bash
uv sync --group airflow
```

Siapin source data dan initial history:

```bash
uv run python scripts/bootstrap_data.py
uv run python scripts/prepare_historical_demand.py
uv run python scripts/build_features.py
```

Training DAG juga butuh MLflow server:

```bash
uv run mlflow server
```

Di terminal lain, start Airflow:

```bash
uv run --group airflow python scripts/start_airflow.py
```

## Daily replay DAG

Buka DAG:

```text
taxi_daily_replay
```

Saat trigger, Airflow kasih parameter:

```text
replay_date = 2025-01-27
```

Flow task:

```text
get_replay_date
      ↓
release_batch
      ↓
validate_batch
      ↓
aggregate_demand
      ↓
rebuild_features
```

### release_batch

Mengambil satu tanggal dari:

```text
data/source/replay/
```

lalu me-release:

```text
data/raw/trips/2025-01-27.parquet
```

### validate_batch

Cek minimal:

```text
batch tidak kosong
timestamp valid
semua trip sesuai replay date
PULocationID tidak kosong
```

Kalau validation gagal, downstream task otomatis nggak lanjut.

### aggregate_demand

Mengubah trip-level batch menjadi:

```text
data/processed/demand/2025-01-27.parquet
```

dengan granularity:

```text
1 row = 1 zone x 1 hour
```

### rebuild_features

Feature dataset dibangun ulang dari history:

```text
2025-01-01
sampai
replay_date terbaru
```

Jadi ketika Jan 27 selesai:

```text
features sampai Jan 27
```

ketika Jan 28 selesai:

```text
features sampai Jan 28
```

## Training DAG

DAG kedua:

```text
taxi_initial_training
```

Flow:

```text
create_snapshot
      ↓
train_model
      ↓
register_candidate
```

### create_snapshot

Task ini menjalankan DVC stage:

```text
dvc repro create_training_snapshot
```

Jadi training input tetap punya dataset version yang jelas.

### train_model

Task ini reuse function yang sama dengan:

```text
scripts/train_with_mlflow.py
```

Output yang diteruskan lewat XCom cuma metadata seperti:

```text
baseline_mae
model_mae
model_run_id
dataset_sha256
model_beats_baseline
```

Model artifact tetap disimpan MLflow, bukan di XCom.

### register_candidate

Kalau:

```text
model MAE < baseline MAE
```

model didaftarkan ke registry sebagai:

```text
challenger
```

Kalau model kalah dari baseline, registration dihentikan.

## Kenapa schedule=None?

Untuk workshop kita sengaja pakai manual trigger.

Alasannya simpel: kita mau bisa demo Jan 27, lalu Jan 28, lalu Jan 29 dalam beberapa menit tanpa nunggu calendar time beneran.

Nanti production version bisa diganti ke daily schedule dan target date diambil dari Airflow logical date.

Historical replay di sini cuma mempercepat waktu, bukan mengubah dependency pipeline.

## Monitoring DAG

DAG ketiga:

```text
taxi_model_monitoring
```

Flow-nya:

```text
evaluate_model
      ↓
maybe_retrain
```

`evaluate_model` baca prediction log, cari ground truth yang sudah tersedia, lalu compare recent MAE dengan validation MAE champion dari MLflow.

Default decision rule:

```text
recent MAE > reference MAE x 1.25
AND
evaluated predictions >= 100
```

Angka ini configurable lewat Airflow params atau environment.

Kalau model masih sehat, `maybe_retrain` berhenti dengan status `not_needed`.

Kalau performa turun:

```text
latest feature dataset
      ↓
runtime training snapshot
      ↓
5-day validation window terbaru
      ↓
MLflow retraining run
      ↓
beat naive baseline?
      ↓ yes
register challenger
```

Runtime snapshot tetap punya nama + SHA256 dan dicatat di MLflow. Kita nggak menjalankan `dvc add` otomatis dari Airflow karena itu bakal memodifikasi repository runtime. DVC tetap dipakai buat reproducible versioned snapshot workflow, sedangkan runtime retraining menyimpan fingerprint dataset di MLflow.

Champion promotion masih manual. Jadi automation berhenti di challenger, bukan langsung ganti production model.
