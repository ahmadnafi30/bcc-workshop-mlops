# Step 5 — Airflow: Dari Command Manual ke DAG yang Bisa Dilihat

Sekarang kita punya beberapa manual steps yang sudah kalian pahami.

Perfect timing buat masuk Airflow.

Kalau kalian belum ngerti manual pipeline, jangan skip ke sini dulu.

Airflow enak dipelajari kalau underlying logic already familiar.

---

# 1. Install Airflow dependency group

~~~bash
uv sync --group airflow
~~~

Ini lebih berat daripada base sync.

First install bisa agak lama.

---

# 2. Start Airflow

~~~bash
uv run --group airflow python scripts/start_airflow.py
~~~

Open:

~~~text
http://localhost:8080
~~~

Standalone mode setup local Airflow environment.

---

# 3. Cari tiga DAG

~~~text
taxi_daily_replay
taxi_initial_training
taxi_model_monitoring
~~~

Kalau salah satu missing, jangan lanjut seolah normal.

DAG missing usually berarti parse/import issue.

---

# 4. Buka taxi_daily_replay

Graph view harus menunjukkan:

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

Coba compare dengan command manual Step 1.

Recognize pattern?

Airflow tidak invent pipeline baru.

Dia arrange pipeline yang sudah ada.

---

# 5. Trigger Jan 27

Masukkan param:

~~~text
replay_date = 2025-01-27
~~~

Trigger.

Observe states.

Typical Airflow color/state akan change selama task running/success/fail.

---

# 6. Klik satu task

Open logs.

Misalnya release_batch.

Lihat actual output.

Jangan treat UI sebagai black box.

Task log adalah salah satu tempat debugging utama.

---

# 7. Validate downstream behavior

Kalau release success lalu validate success, aggregate jalan.

Kalau validation fail, aggregate seharusnya tidak blindly lanjut.

Ini dependency in action.

---

# 8. Check output files

Setelah run:

~~~text
data/raw/trips/2025-01-27.parquet
data/processed/demand/2025-01-27.parquet
~~~

Feature dataset juga rebuilt.

---

# 9. Trigger Jan 28

~~~text
replay_date = 2025-01-28
~~~

Sekarang history extend lagi.

---

# 10. Inspect XCom

Kalau UI expose XCom/task return, lihat.

Yang lewat adalah metadata kecil.

Bukan full taxi DataFrame.

Pertanyaan:

> Kenapa nggak pass DataFrame langsung?

Karena XCom bukan large data channel.

---

# 11. Buka initial training DAG

~~~text
create_snapshot
      ↓
train_model
      ↓
register_candidate
~~~

Coba pikir:

> Kenapa DAG ini terpisah dari daily replay?

Jawaban:

> New data arrival tidak selalu berarti harus train model.

Lifecycle berbeda.

---

# 12. Buka monitoring DAG

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Kita belum perlu trigger sekarang kalau prediction logs belum ada.

Tapi lihat graph dulu.

Nanti di Step 10 kita balik ke sini.

---

# 13. Failure mindset

Kalau DAG fail, jangan bilang:

> “Airflow error.”

Coba lebih specific:

~~~text
Which DAG?
Which run?
Which task?
Which exception?
Which upstream artifact?
~~~

Contoh:

> aggregate_demand failed because input daily parquet missing.

Ini debugging yang jauh lebih actionable.

---

# Mini challenge

Kalau function feature engineering punya bug, apakah fix-nya sebaiknya ditulis langsung di DAG?

Jawaban:

~~~text
No.
Fix reusable logic in src/features,
then DAG continues to call it.
~~~

DAG tetap orchestration layer.

---

# Checkpoint

Kalian harus bisa explain:

- DAG,
- task,
- dependency,
- XCom,
- DAG parsing,
- why DAG thin,
- why multiple DAGs.

Next kita pindah dari training/orchestration ke model serving.
