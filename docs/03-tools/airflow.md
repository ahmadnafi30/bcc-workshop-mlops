# Apache Airflow — Orchestrating the Workflow

## Airflow sering kelihatan intimidating di awal

Ada DAG, task, scheduler, XCom, trigger, run, dependency, task state, dan banyak istilah lain.

Kalau semua dilempar sekaligus memang bikin pusing.

Jadi kita mulai dari problem dulu.

---

# Sebelum Airflow

Kita sebenarnya sudah punya script:

~~~text
simulate_daily_data.py
prepare_daily_demand.py
build_features.py
train_with_mlflow.py
...
~~~

Kita bisa jalankan manual.

Sekali dua kali aman.

Tapi bayangin flow ini harus jalan berkali-kali.

Terus script B gagal.

Apakah script C boleh jalan?

Siapa yang tahu?

Kapan harus retry?

Run kemarin sukses semua atau nggak?

Nah, itu orchestration problem.

---

# Airflow bukan sekadar Python executor

Airflow bukan dipakai karena kita butuh cara menjalankan Python.

Python bisa jalan sendiri.

Airflow dipakai karena kita butuh:

- dependency,
- scheduling,
- retries,
- execution history,
- task-level logs,
- visibility.

Pertanyaan utamanya:

> **What should run, in what order, and what happened during execution?**

---

# Analogi: event coordinator

Bayangin kalian bikin event.

Ada venue setup, sound check, registration, opening, dan speaker session.

Sound check nggak boleh selesai setelah speaker sudah tampil.

Registration mungkin baru mulai setelah venue ready.

Event coordinator tidak melakukan semua pekerjaan teknis sendiri.

Dia coordinate.

Airflow kurang lebih begitu.

---

# DAG itu apa?

DAG = Directed Acyclic Graph.

## Graph

Graph punya node dan edge.

Airflow:

~~~text
node
→ task

edge
→ dependency
~~~

Misalnya:

~~~text
validate_batch
      ↓
aggregate_demand
~~~

Dua task, satu dependency.

## Directed

Dependency punya arah.

~~~text
A → B
~~~

berarti B depends on A.

## Acyclic

Tidak boleh punya cycle.

~~~text
A → B → C → A
~~~

kalau ada loop seperti itu, workflow nggak punya valid execution order.

---

# DAG bukan data

DAG bukan file Parquet.

DAG bukan data contents.

DAG adalah **workflow structure**.

Dia menjelaskan:

~~~text
task mana
depends on
task mana
~~~

---

# DAG kita

Folder:

~~~text
dags/
~~~

Ada tiga:

~~~text
taxi_daily_replay.py
taxi_initial_training.py
taxi_model_monitoring.py
~~~

Masing-masing punya lifecycle berbeda.

---

# Daily replay DAG

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

Kalau validate fail:

~~~text
validate ❌
↓
downstream stop
~~~

Ini data quality gate.

---

# Initial training DAG

~~~text
create_snapshot
      ↓
train_model
      ↓
register_candidate
~~~

Training tidak selalu harus terjadi setiap ada daily batch.

Itu alasan kita tidak bikin satu DAG raksasa.

---

# Monitoring DAG

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

maybe_retrain bisa decide:

~~~text
healthy
→ stop

degraded
→ new snapshot
→ retrain
→ challenger
~~~

No-op adalah valid outcome.

---

# TaskFlow API

Airflow 3 punya authoring API dari airflow.sdk.

Pattern sederhana:

~~~python
@dag(...)
def pipeline():

    @task
    def step_a():
        ...

    @task
    def step_b(value):
        ...

    result = step_a()
    step_b(result)
~~~

Saat DAG parsing, pemanggilan function berdekorator tidak sama dengan ordinary immediate execution.

Airflow membangun task relationship.

Actual body dijalankan saat task instance dieksekusi.

---

# DAG parsing vs execution

Airflow perlu import DAG file untuk tahu structure.

Saat parsing:

- decorators dibaca,
- tasks dibentuk,
- dependencies dibentuk.

Jangan taruh heavy execution di top-level DAG module.

Bad:

~~~python
df = pd.read_parquet("huge.parquet")
model.fit(...)
~~~

karena itu bisa terjadi saat scheduler parse file.

DAG parse harus ringan.

---

# Rule kita: DAG tipis

~~~text
dags/
→ WHEN + ORDER

src/
→ HOW
~~~

Business logic reusable hidup di src.

DAG mostly wrapper + dependency.

Keuntungannya:

- easier to test,
- bisa dipakai tanpa Airflow,
- DAG lebih readable,
- debugging lebih gampang.

---

# XCom

Task kadang perlu pass result kecil.

Contoh:

~~~json
{
  "date": "2025-01-27",
  "rows": 125000,
  "path": "data/raw/trips/2025-01-27.parquet"
}
~~~

Task berikutnya bisa menerima metadata itu via XCom.

---

# Jangan kirim DataFrame besar lewat XCom

XCom bukan large-data transport.

Bad:

~~~text
500 MB DataFrame
↓
XCom
~~~

Better:

~~~text
task A
writes parquet

XCom
passes path + metadata

task B
reads parquet
~~~

Jadi:

~~~text
large data
→ file/object storage

small metadata
→ XCom
~~~

---

# Task boundary

Jangan setiap function jadi task.

Jangan juga semuanya satu task.

Pertanyaan useful:

> “Kalau bagian ini gagal, apakah saya ingin melihat failure-nya secara terpisah?”

Kalau iya, mungkin itu task boundary yang meaningful.

---

# Retry

Airflow bisa retry task.

Tapi retry bukan solusi untuk deterministic bug.

~~~text
temporary network failure
→ retry mungkin useful

logic bug
→ retry 100x tetap bug
~~~

Bedakan transient failure dan logic failure.

---

# schedule=None

DAG workshop manual trigger.

Kenapa?

Karena kita historical replay.

Presenter bisa trigger Jan 27 lalu Jan 28 dalam hitungan menit.

Production nanti bisa punya daily schedule atau event trigger.

Workshop prioritizes visibility.

---

# Params

Daily DAG menerima replay_date.

Kenapa param, bukan edit code?

Karena runtime input seharusnya configurable tanpa commit baru.

~~~text
workflow definition
vs
workflow run configuration
~~~

---

# Idempotency

Pipeline sering rerun.

Bisa karena:

- fail,
- retry,
- backfill,
- recovery.

Idealnya same logical date menghasilkan predictable output, bukan duplicate random rows.

Itu idempotency mindset.

---

# Airflow UI

Yang perlu kalian explore:

## DAG list

Apakah DAG ke-detect?

## Graph

Dependency terlihat?

## Runs

Run history.

## Task logs

Exact failure.

Jangan debug whole Airflow kalau yang fail cuma satu task.

---

# Airflow vs GitHub Actions

Ini wajib clear.

~~~text
Airflow
→ data / ML workflow orchestration

GitHub Actions
→ source repository automation
~~~

New daily taxi batch cocok ke Airflow.

New pull request cocok ke GitHub Actions.

---

# Cara bikin DAG baru dari nol

1. Tulis flow plain language.
2. Tentukan task boundary.
3. Buat reusable function di src.
4. Test function tanpa Airflow.
5. Wrap ke @task.
6. Connect dependency.
7. Tentukan runtime params.
8. Pikirkan rerun/idempotency.

Jangan mulai dari decorator dulu.

Mulai dari workflow logic.

---

# Takeaway

Kalau hanya ingat satu kalimat:

> **Airflow mengatur workflow, bukan menggantikan business logic.**

Dan kalau ingat dua:

> **DAG sebaiknya tipis, reusable logic sebaiknya hidup di src/.**
