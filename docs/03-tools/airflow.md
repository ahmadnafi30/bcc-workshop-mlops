# Apache Airflow — Dari Run Script Satu-Satu ke Workflow yang Bisa Diatur

Airflow sering kelihatan intimidating buat newbie karena istilahnya banyak: DAG, task, scheduler, XCom, run, state, trigger, operator.

Kalau semuanya dilempar sekaligus, ya wajar bingung.

Jadi kita mulai dari problem.

---

## Bayangin pipeline tanpa Airflow

Kalian punya lima command:

~~~text
1. release data
2. validate data
3. aggregate demand
4. build features
5. train model
~~~

Kalau sekali jalan manual, masih gampang.

Sekarang tambah complexity.

Step 2 gagal. Harus ulang dari awal atau lanjut dari mana?

Step 3 butuh output step 1 dan 2.

Step 4 harus jalan berulang.

Step 5 cuma boleh jalan kalau performance turun.

Sekarang kita butuh sesuatu yang ngerti:

~~~text
dependency
execution order
state
retry
schedule
logs
~~~

Itulah orchestration.

Airflow adalah workflow orchestrator.

---

## Analogi: production manager film

Bayangin bikin film.

Ada set team, lighting, camera, actors, editor.

Production manager nggak pegang kamera dan nggak edit footage.

Dia coordinate:

~~~text
set ready
↓
lighting ready
↓
camera roll
↓
actor perform
↓
footage ke editor
~~~

Airflow mirip production manager.

Actual pekerjaan tetap dilakukan reusable function/script.

Airflow coordinate **kapan**, **urutan**, dan **state**.

Makanya kita menghindari pattern:

> “Semua business logic ditulis di DAG.”

---

## Apa itu DAG?

DAG = Directed Acyclic Graph.

Kita pecah.

### Graph

Graph punya node dan edge.

Di Airflow:

~~~text
node
→ task

edge
→ dependency
~~~

### Directed

Arah matters.

~~~text
validate → aggregate
~~~

artinya aggregate depend on validate.

### Acyclic

Tidak boleh cycle.

Bad:

~~~text
A → B → C → A
~~~

Kalau ada cycle, workflow tidak punya execution order yang valid.

---

## DAG bukan data

DAG itu **workflow definition**.

Dia mendeskripsikan:

~~~text
task apa?
dependency bagaimana?
parameter apa?
kapan jalan?
~~~

Bukan file dataset.

---

## Task itu apa?

Task = satu unit of work.

Contoh:

~~~text
release_batch
validate_batch
aggregate_demand
~~~

Task boundary yang bagus biasanya punya satu responsibility jelas.

Kenapa jangan satu giant task?

Misalnya:

~~~text
download + validate + aggregate + features + train
~~~

Kalau gagal, kita cuma tahu big_task failed.

Tapi gagal di mana?

Boundary yang jelas bikin debugging dan retry lebih bagus.

---

## DAG pertama: taxi_daily_replay

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

### get_replay_date

Resolve date yang mau direplay.

Karena workshop historical simulation, presenter bisa trigger Jan 27 lalu Jan 28 dalam beberapa menit tanpa edit code.

### release_batch

Ambil historical data dari replay source lalu materialize seolah data baru datang.

### validate_batch

Fail early kalau input invalid.

Kenapa validation sebelum transform? Karena corrupted input jangan dibiarkan lanjut ke downstream pipeline.

### aggregate_demand

Trip-level rows jadi hourly zone demand.

### rebuild_features

History bertambah, jadi feature table diperbarui.

---

## DAG kedua: taxi_initial_training

~~~text
create_snapshot
      ↓
train_model
      ↓
register_candidate
~~~

Kenapa terpisah dari daily replay?

Karena:

> **New data arrival tidak selalu berarti harus retrain.**

Kalau setiap daily batch langsung retrain, model train terus tanpa evidence bahwa retraining memang perlu.

Data pipeline dan training lifecycle punya trigger berbeda.

---

## DAG ketiga: taxi_model_monitoring

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Yang menarik: maybe_retrain bisa memilih tidak melakukan training.

Kalau model sehat:

~~~text
evaluate
↓
not_needed
↓
finish
~~~

Kalau degraded:

~~~text
evaluate
↓
retrain recommended
↓
new snapshot
↓
train
↓
register challenger
~~~

No-op bisa menjadi outcome automation yang benar.

Automation bukan berarti “selalu melakukan sesuatu”.

---

## TaskFlow API

Simplified:

~~~python
from airflow.sdk import dag, task

@dag(...)
def my_pipeline():

    @task
    def first():
        return {"rows": 100}

    @task
    def second(info):
        print(info["rows"])

    result = first()
    second(result)

my_pipeline()
~~~

Syntax-nya kelihatan seperti function biasa, tapi saat DAG parsing Airflow membangun graph task dependency.

---

## XCom

XCom dipakai untuk task communication.

Contoh task return:

~~~text
date
rows
path
status
~~~

Itu metadata kecil.

Kenapa kita nggak pass full DataFrame?

Karena XCom bukan large data transport.

Bad:

~~~text
huge DataFrame
↓
serialize
↓
metadata database
~~~

Better:

~~~text
large data
→ parquet / storage

XCom
→ reference + metadata
~~~

Ini design principle penting banget.

---

## Kenapa DAG harus tipis?

Rule project kita:

~~~text
dags/
→ WHEN + IN WHAT ORDER

src/
→ HOW
~~~

Misalnya feature engineering bug.

Fix reusable function di src/features.

Jangan copy 200 line Pandas logic ke DAG.

Benefit:

- bisa unit test tanpa Airflow,
- bisa dipanggil script,
- lebih reusable,
- DAG lebih readable.

---

## Cara design DAG dari nol

Jangan mulai dari syntax Airflow.

Mulai dari whiteboard.

### Step 1 — tulis proses natural language

~~~text
download
validate
clean
aggregate
save
~~~

### Step 2 — tentukan boundary

Tanya:

> “Kalau step ini gagal, apakah saya ingin tahu dan retry secara terpisah?”

Kalau iya, mungkin cocok jadi task.

### Step 3 — define dependency

~~~text
validate depends on download
aggregate depends on validate
~~~

### Step 4 — implement reusable logic

Di luar DAG.

### Step 5 — wire ke Airflow

Baru setelah itu bikin orchestration.

---

## Scheduling

Production Airflow sering daily/hourly.

Workshop kita manual trigger karena historical replay.

Kalau pakai real clock, kita harus nunggu besok buat demo Jan 28. Nggak lucu. 😭

Manual trigger bikin lifecycle bisa dipercepat tanpa mengubah dependency logic.

---

## Idempotency

Retry itu normal.

Task sebaiknya aman dijalankan ulang.

~~~text
run Jan 27
→ output A

rerun Jan 27
→ output A lagi
~~~

bukan duplicate rows atau random corruption.

Idempotency bikin retry lebih aman.

---

## Airflow vs GitHub Actions

Sering ketuker karena dua-duanya automation.

~~~text
Airflow
→ data / ML workflow

GitHub Actions
→ repository change workflow
~~~

Contoh:

~~~text
new taxi batch
→ Airflow

new pull request
→ GitHub Actions
~~~

---

## Debugging mindset

Kalau Airflow gagal, jangan bilang:

> “Airflow error.”

Tanya lebih specific:

~~~text
DAG mana?
run mana?
task mana?
exception apa?
input artifact ada?
dependency service reachable?
~~~

Contoh actionable:

> aggregate_demand failed karena daily parquet belum ada.

Itu jauh lebih gampang ditangani.

---

## Checkpoint

Setelah section ini, coba jawab:

1. DAG itu apa?
2. Task itu apa?
3. Dependency itu apa?
4. XCom dipakai buat apa?
5. Kenapa DataFrame besar jangan lewat XCom?
6. Kenapa DAG kita tipis?
7. Kenapa daily replay dan training dipisah?
8. Airflow beda apa dengan GitHub Actions?

Kalau bisa jawab, core Airflow concept-nya sudah kebayang.
