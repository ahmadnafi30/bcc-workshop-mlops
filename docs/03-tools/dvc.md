# DVC and Training Snapshots

Sekarang feature dataset kita sudah ada, tapi ada satu problem:

> model ini sebenarnya ditrain pakai dataset yang mana?

Kalau file `taxi_demand_features.parquet` berubah terus, nama file-nya tetap sama. Dari nama file doang kita nggak bisa tahu isi dataset waktu model version tertentu dibuat.

Di sinilah DVC dipakai.

## Git, DVC, dan MLflow bedanya apa?

Versi gampangnya:

| Tool | Yang kita version / track |
| --- | --- |
| Git | code, config, docs |
| DVC | dataset dan pipeline output |
| MLflow | experiment, metric, parameter, model |

Jadi ketiganya bukan saling menggantikan.

Flow project kita:

```text
Git commit
   ↓
code version

Feature Dataset
   ↓
DVC
   ↓
training snapshot

Training Snapshot
   ↓
Model Training
   ↓
MLflow
   ↓
params + metrics + model artifact
```

## Training snapshot

Feature dataset utama ada di:

```text
data/features/taxi_demand_features.parquet
```

Sebelum training kita bikin snapshot:

```text
data/snapshots/training/
└── taxi_demand_2025-01-26.parquet
```

Nama tanggal itu adalah cutoff data yang boleh masuk ke initial training cycle.

Jadi walaupun feature dataset nanti bertambah karena production replay, model initial tetap bisa direproduce dari snapshot lama.

## DVC stage

Project punya:

```text
dvc.yaml
```

dengan stage:

```text
create_training_snapshot
```

Jalankan:

```bash
uv run dvc repro create_training_snapshot
```

DVC bakal lihat dependency:

```text
data/features/taxi_demand_features.parquet
scripts/create_training_snapshot.py
src/data_versioning/snapshot.py
```

dan menghasilkan:

```text
data/snapshots/training/taxi_demand_2025-01-26.parquet
```

Kalau input dan code belum berubah, DVC bisa tahu stage itu nggak perlu dijalankan ulang.

## dvc.lock

Setelah `dvc repro` pertama, DVC bakal generate:

```text
dvc.lock
```

File ini yang nyimpen checksum dependency dan output pipeline.

`dvc.lock` justru **masuk Git**.

Jadi Git commit tertentu bisa nunjuk ke exact dataset state yang dipakai DVC.

## DVC cache

File data yang di-track DVC disimpan juga di local cache:

```text
.dvc/cache/
```

Folder cache nggak masuk Git.

Untuk workshop kita belum setup shared remote storage dulu. Fokus awalnya adalah memahami versioning dan reproducibility lokal.

Nanti kalau project ini mau dipakai tim beneran, DVC remote bisa diarahkan ke object storage seperti S3 atau storage lain yang didukung DVC.

## Snapshot fingerprint di MLflow

Selain DVC checksum, script kita juga hitung SHA256 snapshot.

Contohnya:

```text
dataset_snapshot = taxi_demand_2025-01-26.parquet
dataset_sha256   = a1b2c3...
dataset_rows     = ...
dataset_zones    = ...
```

Metadata ini ikut dilog ke MLflow.

Jadi dari satu MLflow run kita bisa jawab:

```text
model apa?
hyperparameter berapa?
metric berapa?
dataset snapshot yang mana?
fingerprint dataset apa?
```

Hubungannya jadi jelas:

```text
DVC
"ini dataset version yang dipakai"

MLflow
"ini hasil experiment dari dataset itu"
```

## Full flow sebelum training

Untuk initial model:

```bash
uv run python scripts/bootstrap_data.py
uv run python scripts/prepare_historical_demand.py
uv run python scripts/build_features.py
uv run dvc repro create_training_snapshot
uv run python scripts/train_model.py
```

Kalau pakai MLflow:

```bash
uv run mlflow server
```

lalu di terminal lain:

```bash
uv run python scripts/train_with_mlflow.py
```

## Kenapa nggak DVC semua raw data?

Bisa saja, tapi untuk workshop kita sengaja fokus versioning pada data yang paling dekat dengan training.

Raw TLC data besar dan sebenarnya bisa di-download ulang dari source official.

Yang lebih penting buat reproducibility model adalah:

```text
exact training snapshot
```

Nanti kalau scope project diperluas, raw dan intermediate dataset juga bisa ikut dimanage DVC.
