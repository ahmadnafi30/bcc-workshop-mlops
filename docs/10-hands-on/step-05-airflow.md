# Step 5 — Airflow: Dari Pipeline Manual ke DAG yang Bisa Dilihat dan Di-debug

Sampai sekarang kalian sudah menjalankan banyak command manual.

Bagus.

Justru sekarang Airflow akan terasa berguna.

Kalau dari awal langsung Airflow, peserta cuma lihat UI tanpa ngerti underlying operation.

---

## Goal

Setelah step ini:

- Airflow local jalan,
- tiga DAG visible,
- daily replay dipicu,
- kalian ngerti task state/log,
- ngerti XCom,
- ngerti kenapa DAG dipisah.

---

## 1. Install Airflow group

~~~bash
uv sync --group airflow
~~~

First install bisa lama.

Airflow dependency tree memang lebih berat.

---

## 2. Start Airflow

~~~bash
uv run --group airflow python scripts/start_airflow.py
~~~

Open:

~~~text
http://localhost:8080
~~~

---

## 3. Sebelum klik apa-apa

Cari tiga DAG:

~~~text
taxi_daily_replay
taxi_initial_training
taxi_model_monitoring
~~~

Pertanyaan:

> “Kenapa tiga, bukan satu?”

Coba jawab dulu.

Hint:

~~~text
new data
≠
always retrain
~~~

---

## 4. Open daily replay Graph

Expected:

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

Coba mapping ke Step 1 manual commands.

Recognize?

Airflow cuma orchestrate flow yang sudah kalian kenal.

---

## 5. Trigger Jan 27

Parameter:

~~~text
replay_date = 2025-01-27
~~~

Trigger.

Jangan langsung pindah tab.

Observe state.

Task bisa:

~~~text
scheduled
running
success
failed
~~~

Lifecycle state ini salah satu value Airflow.

---

## 6. Klik release_batch

Open logs.

Cari output path dan row count.

Pertanyaan:

> “Kalau release_batch fail, validate_batch harus jalan nggak?”

No.

Dependency prevent downstream execution.

---

## 7. Inspect XCom

Kalau UI expose output metadata, lihat.

Expected small info:

~~~text
date
rows
path
~~~

Kenapa bukan DataFrame?

Karena XCom bukan heavy data channel.

---

## 8. Validate file system

Setelah success:

~~~text
data/raw/trips/2025-01-27.parquet
data/processed/demand/2025-01-27.parquet
~~~

Airflow UI green sebaiknya correlate dengan actual artifact.

Jangan trust UI blindly.

---

## 9. Trigger Jan 28

Repeat.

Sekarang history maju.

Observe bahwa pipeline logic same, logical date beda.

Ini parameterized workflow.

---

## 10. Open initial training DAG

~~~text
create_snapshot
↓
train_model
↓
register_candidate
~~~

Question:

> “Kenapa daily replay nggak otomatis connect langsung ke training DAG?”

Karena retraining trigger bukan setiap new data.

---

## 11. Open monitoring DAG

~~~text
evaluate_model
↓
maybe_retrain
~~~

Nanti balik lagi di Step 10.

Sekarang cukup pahami graph.

---

## 12. Simulate debugging mindset

Bayangin validate_batch merah.

Jangan bilang:

> “Airflow broken.”

Tanya:

~~~text
input path?
schema?
date?
stack trace?
upstream return?
~~~

Specific problem lebih mudah di-debug.

---

## Mini challenge

Kalau feature engineering logic salah, file mana yang harus diubah?

Jawaban:

~~~text
src/features
~~~

Bukan copy fix ke DAG.

DAG tetap orchestration.

---

## Checkpoint

Explain:

- DAG,
- task,
- dependency,
- state,
- XCom,
- task log,
- manual trigger,
- why separate DAG.

Kalau clear, kita move ke serving.
