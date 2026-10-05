# Data Pipeline Part 3 — Airflow in Our Project

## Dari manual scripts menjadi orchestrated workflow

Sampai titik ini, kita sudah bisa:

~~~text
release date
validate
aggregate
build features
~~~

semua manual.

Sekarang Airflow masuk bukan untuk mengganti logic, tapi untuk mengatur lifecycle execution.

---

# Daily replay DAG

File:

~~~text
dags/taxi_daily_replay.py
~~~

Flow:

~~~text
get_replay_date
      ↓
release_batch
      ↓
validate_batch
      ↓
aggregate_demand
      ↓
rebuild_features
~~~

Mari kita mapping ke business meaning.

---

# get_replay_date

Resolve runtime param:

~~~text
2025-01-27
~~~

Ini membuat satu run punya explicit logical input.

Kenapa nggak hard-code date?

Karena workflow definition harus reusable.

---

# release_batch

Memanggil historical replay logic.

Hasil actual data ditulis ke file.

Return value kecil seperti:

~~~text
date
rows
path
~~~

bisa lewat XCom.

---

# validate_batch

Check batch contract.

Kalau fail:

~~~text
downstream tidak lanjut
~~~

Ini exactly why task separation berguna.

Failure boundary terlihat jelas di UI.

---

# aggregate_demand

Trip-level data menjadi hourly zone demand.

Ini reuse function dari src.

DAG tidak implement ulang groupby logic.

---

# rebuild_features

Setelah processed date baru available, feature dataset update.

Sekarang historical features include latest date.

---

# Initial training DAG

File:

~~~text
dags/taxi_initial_training.py
~~~

Flow:

~~~text
create_snapshot
      ↓
train_model
      ↓
register_candidate
~~~

Kenapa dipisah dari daily replay?

Karena arrival data tidak selalu berarti harus retrain.

Kalau tiap daily batch auto-train tanpa condition, system boros dan governance-nya jelek.

---

# Monitoring DAG

File:

~~~text
dags/taxi_model_monitoring.py
~~~

Flow sederhana:

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Di dalam maybe_retrain ada branching logic conceptual:

~~~text
performance okay
→ no-op

performance degraded
→ create snapshot
→ train
→ register challenger
~~~

---

# Why no automatic champion promotion?

Karena retraining adalah technical action.

Promotion adalah governance decision.

Mereka related tapi nggak identik.

System boleh otomatis create candidate baru.

Tapi approval production tetap explicit.

---

# Runtime retraining snapshot

Initial DVC snapshot punya versioned workflow.

Saat runtime Airflow retraining, kita tidak menjalankan DVC add yang mengubah repo state.

Instead:

- create deterministic snapshot file,
- calculate SHA256,
- log fingerprint ke MLflow.

Ini membuat runtime automation tidak mutate Git repository.

---

# XCom design

Yang lewat XCom:

~~~text
path
date
row count
metric summary
run ID
~~~

Yang tidak:

~~~text
DataFrame besar
Parquet content
model binary
~~~

File storage tetap tempat large artifacts.

---

# Why this architecture matters

Kalau DAG terlalu banyak logic:

- sulit test,
- sulit reuse,
- parse heavy,
- Airflow jadi dependency untuk semua.

Kalau DAG tipis:

~~~text
src function
↓
test directly
↓
wrap in task
~~~

much cleaner.

---

# What should participants inspect in UI?

## Graph View

Lihat dependency.

## Task Logs

Lihat actual command/function outcome.

## Params

Pastikan replay date sesuai.

## Run History

Bandingkan Jan 27 dan Jan 28.

## Failure State

Kalau ada task gagal, lihat downstream behavior.

---

# Airflow is not the data store

Airflow coordinate.

Data ada di:

~~~text
data/raw
data/processed
data/features
data/snapshots
~~~

MLflow punya model artifacts.

Prometheus punya metrics.

Airflow sendiri bukan central place untuk menyimpan semua data.

---

# Takeaway

Kalau kalian lihat DAG file dan bisa bilang:

> “Oh ini cuma orchestration wrapper dari reusable functions.”

itu exactly design yang kita mau.
