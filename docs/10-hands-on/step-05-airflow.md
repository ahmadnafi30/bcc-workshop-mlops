# Step 5 — Airflow: Dari Pipeline Manual ke Workflow yang Bisa Dilihat, Diulang, dan Di-debug

!!! tip "Praktik Airflow + DVC terbaru"
    Ikuti [panduan workflow dan optimasi](../05-data-pipeline/airflow-dvc-workshop.md) untuk dua stage DVC, params.json, pemisahan training/replay, cache features, pool, retry, dan UI tour.


Nah peers, sekarang timing-nya pas banget buat masuk Airflow.

Kenapa baru sekarang?

Karena dari Step 1 sampai Step 4 kalian sudah pernah menjalankan proses dasarnya secara manual. Kalian sudah tahu rasanya release data, prepare demand, build features, bikin snapshot, train model, dan track experiment.

Itu penting.

Kalau Airflow dikenalkan sebelum kalian tahu proses manualnya, yang terlihat cuma kotak-kotak di UI:

~~~text
task A
↓
task B
↓
task C
~~~

tapi kalian nggak ngerti kotak itu sebenarnya melakukan apa.

Sekarang kita punya context.

---

## Cara berpikir setelah step ini

Setelah selesai, kalian bukan cuma bisa click Trigger DAG.

Kalian harus bisa menjelaskan:

- kenapa project punya tiga DAG;
- satu task responsibility-nya apa;
- dependency terbentuk dari mana;
- parameter replay_date dipakai bagaimana;
- apa yang lewat XCom;
- kenapa DataFrame besar tidak lewat XCom;
- kenapa business logic tetap di src;
- gimana membaca task log;
- gimana berpikir kalau satu task fail;
- apa arti idempotent dalam workflow replay.

Jadi target kita bukan:

> “Airflow UI berhasil kebuka.”

Target kita:

> “Saya ngerti kenapa graph ini bentuknya seperti ini.”

---

## Hasil yang perlu terlihat di laptop

Setelah step ini:

- Airflow local jalan,
- tiga DAG visible,
- daily replay dipicu,
- kalian ngerti task state/log,
- ngerti XCom,
- ngerti kenapa DAG dipisah.

---

## 1. Install Airflow group

Bagian ini hanya diperlukan untuk mode standalone lokal. Jika kamu memakai Airflow Docker Compose, skip instalasi group ini dan lanjut ke catatan Compose di bagian start.

Core environment kita sengaja nggak langsung install Airflow karena dependency-nya cukup berat.

Run:

~~~bash
uv sync --group airflow
~~~

First install bisa agak lama.

Itu normal.

Sambil menunggu, coba ingat lagi perbedaan:

~~~text
uv sync
→ core project + dev environment

uv sync --group airflow
→ core project + Airflow dependencies
~~~

Kenapa dipisah?

Karena tidak semua task di repo butuh Airflow. Participant yang cuma mau run feature engineering nggak perlu bayar installation cost Airflow dari awal.

---

## 2. Start Airflow lokal (standalone)

Panduan langkah ini memakai Airflow lokal. Start:

~~~bash
uv run --group airflow python scripts/start_airflow.py
~~~

Buka `http://localhost:8080`. Password awal muncul di terminal saat pertama kali Airflow dijalankan. Jika terlewat, cek file `.airflow/simple_auth_manager_passwords.json.generated` di root repo.

!!! info "Kalau workshop-mu memakai Docker Compose"
    Jangan start standalone lokal bersamaan. Compose dan standalone menyimpan metadata serta run history di tempat berbeda, sehingga UI-nya bisa tampak seperti dua Airflow yang berbeda.

    Start service Compose lalu cek port host:

    ~~~bash
    docker compose up -d --build airflow
    docker compose ps airflow
    ~~~

    Buka port di sisi kiri pemetaan `PORTS`. Jika output menunjukkan `127.0.0.1:18081->8080/tcp`, gunakan `http://localhost:18081`. Untuk melihat credential Compose, jalankan `docker compose exec airflow cat /airflow/simple_auth_manager_passwords.json.generated`.

    Jika ingin menjalankan DAG `taxi_initial_training` di container, aktifkan mode DVC tanpa SCM terlebih dahulu karena image tidak menyertakan folder `.git`:

    ~~~bash
    docker compose exec airflow dvc config core.no_scm true --local
    ~~~

    Ulangi konfigurasi ini jika container dibuat ulang. Konfigurasi hanya berlaku di container; latihan versioning DVC pada host tetap memakai Git checkout.

Jangan langsung click semua menu. Pause sebentar. Pertanyaan pertama:

> “Airflow sekarang sebenarnya tahu DAG kita dari mana?”

Jawabannya: dari DAG files yang ada di folder project.

Project kita punya tiga:

~~~text
taxi_daily_replay
taxi_initial_training
taxi_model_monitoring
~~~

Kalau salah satu nggak muncul, jangan lanjut seolah normal.

Itu berarti ada kemungkinan:

- DAG parsing error;
- import error;
- Airflow environment belum benar;
- file tidak terbaca.

---

## 3. Kenapa ada tiga DAG, bukan satu DAG super panjang?

Coba bayangin satu mega DAG:

~~~text
new data
↓
aggregate
↓
features
↓
train
↓
register
↓
monitor
↓
retrain
↓
promote
~~~

Kelihatannya lengkap.

Tapi logic trigger-nya aneh.

Apakah setiap data baru harus langsung train model?

Tidak.

Apakah setiap monitoring run harus release new data?

Juga tidak.

Jadi kita pisah berdasarkan lifecycle responsibility.

### taxi_daily_replay

Trigger concept:

> “Ada satu logical production day baru yang mau direlease.”

### taxi_initial_training

Trigger concept:

> “Kita ingin membuat initial candidate model dari reproducible snapshot.”

### taxi_model_monitoring

Trigger concept:

> “Kita ingin evaluate champion dan decide apakah retraining perlu.”

Ini desain yang jauh lebih sehat daripada satu DAG raksasa.

---

## 4. Open daily replay Graph

Masuk Graph view.

Expected flow:

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

Sekarang coba mapping dengan manual flow yang sebelumnya kalian jalankan.

~~~text
simulate_daily_data.py
→ release_batch

validation
→ validate_batch

prepare_daily_demand.py
→ aggregate_demand

build_features.py
→ rebuild_features
~~~

Nah, ini moment penting:

> Airflow tidak menciptakan data logic baru. Airflow meng-orchestrate logic yang sudah kita punya.

---

## 5. Buka source DAG sambil lihat Graph

File:

~~~text
dags/taxi_daily_replay.py
~~~

Kalian akan lihat decorator:

~~~python
@dag(
    dag_id="taxi_daily_replay",
    schedule=None,
    ...
)
~~~

Apa arti schedule=None?

Workshop kita pakai manual trigger.

Kenapa?

Karena logical time kita historical.

Kita mau bisa:

~~~text
09:00 real-world time
→ replay 2025-01-27

09:10 real-world time
→ replay 2025-01-28
~~~

Kalau pakai schedule real harian, kita harus nunggu besok buat demo tanggal berikutnya.

Historical replay mempercepat clock, bukan mengubah dependency logic.

---

## 6. Param replay_date

DAG punya param:

~~~text
replay_date
~~~

Default:

~~~text
2025-01-27
~~~

Kenapa parameter lebih bagus daripada edit source code setiap demo?

Bad:

~~~text
ubah Python file ke Jan 27
run
ubah file ke Jan 28
run
~~~

Sekarang Git diff penuh perubahan yang sebenarnya cuma runtime input.

Better:

~~~text
same DAG definition
+
different run parameter
~~~

Parameter memisahkan workflow definition dari runtime value.

---

## 7. Task get_replay_date

Actual logic membaca Airflow context:

~~~text
context
↓
params
↓
replay_date
~~~

Output task ini string tanggal.

Kecil banget.

Kenapa sampai dibuat task sendiri?

Karena dia membuat runtime input visible dalam graph dan bisa menjadi upstream dependency untuk task berikutnya.

---

## 8. Task release_batch

Task ini call reusable function:

~~~text
release_replay_batch
~~~

Actual logic ada di:

~~~text
src/orchestration/daily_pipeline.py
~~~

Function menentukan monthly source berdasarkan date.

Misalnya:

~~~text
replay_date = 2025-01-27
↓
month = 2025-01
↓
source = yellow_tripdata_2025-01.parquet
↓
output = data/raw/trips/2025-01-27.parquet
~~~

Jadi DAG tidak punya Pandas logic untuk filter daily rows.

Dia delegate.

---

## 9. Sebelum trigger: predict dulu apa yang akan terjadi

Kita trigger:

~~~text
replay_date = 2025-01-27
~~~

Sebelum click Trigger, coba jawab:

1. File raw apa yang akan muncul?
2. File processed apa yang akan muncul?
3. Feature dataset akan berhenti sampai tanggal mana?
4. Kalau release_batch fail, apakah aggregate_demand boleh jalan?

Expected reasoning:

~~~text
raw:
data/raw/trips/2025-01-27.parquet

processed:
data/processed/demand/2025-01-27.parquet

features:
rebuilt through Jan 27

upstream fail:
downstream blocked
~~~

Baru trigger.

Learning lebih meaningful kalau kalian punya hypothesis sebelum lihat result.

---

## 10. Observe task states

Saat DAG run, task bisa berada di state seperti:

~~~text
scheduled
queued
running
success
failed
skipped
~~~

Warna di UI bukan dekorasi.

State memberi observability ke workflow.

Kalau manual Bash sequence, beberapa jam kemudian kalian mungkin lupa command mana fail.

Airflow persist run/task state.

---

## 11. Buka release_batch logs

Click task.

Open log.

Jangan cuma cari tulisan success.

Cari:

- logical date;
- output path;
- row count;
- exception kalau ada.

Kalau output bilang file Jan 27 dibuat, check juga filesystem.

Green task state dan actual artifact sebaiknya correlate.

---

## 12. validate_batch dan fail-fast thinking

Task berikutnya validate raw batch.

Kenapa nggak langsung aggregate?

Bayangin source batch ternyata:

- kosong;
- tanggal salah;
- schema missing;
- timestamp invalid.

Kalau langsung transform, problem bisa menyebar lebih jauh.

Flow sehat:

~~~text
ingest
↓
validate
↓
transform
~~~

Fail early memberi error lebih dekat ke root cause.

---

## 13. Detail actual code: dependency metadata yang nggak dibaca

Di DAG kalian akan lihat validate_batch menerima release_info.

Di dalam function ada assignment ke underscore karena content release_info memang tidak dibutuhkan validation logic.

Pertanyaan natural:

> “Kalau isi metadata-nya nggak dipakai, kenapa tetap dikirim?”

Karena object tersebut membentuk task dependency.

~~~text
release_batch
↓ output reference
validate_batch
~~~

Validation bisa menemukan file secara deterministic dari replay_date, tapi dependency tetap explicit.

Jadi output di sini punya dua fungsi potensial:

~~~text
data value
atau
dependency signal
~~~

Ini subtle, tapi bagus banget buat memahami orchestration.

---

## 14. XCom — apa yang sebenarnya berpindah?

Task return dictionary kecil.

Contoh aggregation metadata:

~~~text
date
rows
zones
pickups
path
~~~

Ini cocok buat XCom.

Sekarang bayangin return full taxi DataFrame jutaan rows.

Airflow harus serialize dan menyimpan data besar lewat metadata backend.

Bad idea.

Mental model:

~~~text
XCom
→ sticky note

Parquet
→ actual package
~~~

Sticky note bilang:

> “Paket ada di path ini, rows sekian.”

Sticky note bukan tempat menaruh isi seluruh gudang.

---

## 15. aggregate_demand

Task membaca daily trip parquet + zone lookup lalu reuse aggregate_hourly_demand.

Output complete hourly demand.

Airflow nggak perlu ngerti detail complete zone-hour grid.

Itu domain logic preprocessing.

Again:

~~~text
Airflow
→ orchestration

preprocessing module
→ transformation semantics
~~~

---

## 16. rebuild_features

Setelah daily demand baru tersedia, feature dataset dibangun ulang dari history start sampai replay_date.

Kenapa nggak cuma build feature hari baru?

Karena lag/rolling punya history dependency.

Untuk workshop, rebuild relevant history lebih simple dan reliable daripada incremental feature update.

Production scale besar mungkin optimize incremental compute.

Correctness dulu, optimization nanti.

---

## 17. Trigger Jan 28

Setelah Jan 27 green, trigger Jan 28.

Sebelum run, predict:

~~~text
raw Jan 28
processed Jan 28
feature dataset extends to Jan 28
~~~

DAG sama.

Parameter beda.

Ini reusable workflow definition.

---

## 18. Idempotency experiment

Apa yang terjadi kalau Jan 28 di-trigger lagi?

Workflow sebaiknya menghasilkan state yang predictable, bukan duplicate random data.

Retry itu normal.

Network transient fail, worker restart, atau rerun manual bisa terjadi.

Idempotency principle:

> Rerun logical operation yang sama harus aman dan predictable.

---

## 19. Buka taxi_initial_training

Graph:

~~~text
create_snapshot
↓
train_model
↓
register_candidate
~~~

create_snapshot menjalankan DVC repro.

Artinya training tidak asal baca moving latest file.

train_model log baseline + candidate ke MLflow.

register_candidate punya gate:

~~~text
model beat baseline?
├── no  → not_registered
└── yes → register challenger
~~~

Jadi Airflow meng-orchestrate model lifecycle policy, bukan sekadar train.py.

---

## 20. Kenapa register_candidate task terpisah?

Kalau training success tapi Registry unreachable, failure-nya beda dari model training failure.

Task boundary membuat incident lebih observable:

~~~text
train_model
✅

register_candidate
❌
~~~

Kita jadi tahu layer mana yang perlu di-debug.

---

## 21. Buka taxi_model_monitoring

Graph:

~~~text
evaluate_model
↓
maybe_retrain
~~~

Parameter:

~~~text
degradation_multiplier
min_samples
recent_limit
~~~

Kenapa configurable?

Supaya monitoring policy bisa dieksperimenkan tanpa edit source.

Dalam production, policy change tetap sebaiknya governed.

---

## 22. No-op adalah valid automation result

Kalau result:

~~~text
retrain_recommended = false
~~~

maybe_retrain return not_needed.

DAG success.

Apakah automation gagal karena nggak bikin model baru?

No.

Decision itu sendiri adalah work.

Automation yang selalu harus menghasilkan action justru suspicious.

---

## 23. Airflow vs script — value tambahannya apa?

Manual script sudah bisa melakukan operation.

Airflow menambah:

- dependency graph;
- task state;
- run history;
- logs;
- parameterized runs;
- retry/scheduling capability;
- UI visibility.

Jadi Airflow bukan pengganti Python.

Airflow meng-orchestrate Python work.

---

## 24. Controlled failure exercise

Kalau workshop time cukup, lakukan safe failure.

Misalnya trigger logical date yang source-nya belum siap di local copy.

Observe:

1. Task mana fail?
2. Downstream apa yang tidak jalan?
3. Log bilang apa?
4. Setelah dependency fixed, apakah perlu ulang semua?

Failure exercise sering lebih mendidik daripada hanya happy path.

Pastikan state dipulihkan setelah demo.

---

## 25. Debugging checklist

Kalau DAG nggak muncul:

~~~text
cek import
cek parse error
cek Airflow dependency
~~~

Kalau DAG muncul tapi task fail:

~~~text
which run?
which task?
what exception?
input path ada?
upstream result?
dependency service reachable?
~~~

Kalau task green tapi output salah:

~~~text
inspect generated artifact
inspect reusable domain function
run function/script manually
~~~

Problem task tidak selalu berarti problem Airflow.

---

## Mini discussion

### Scenario A

Feature engineering logic salah.

Fix di src/features, bukan copy fix ke DAG.

### Scenario B

aggregate_demand harus menunggu validation.

Concern-nya dependency DAG.

### Scenario C

Daily pipeline mau dijadwalkan jam 02:00.

Concern-nya Airflow schedule.

### Scenario D

Prediction endpoint berubah.

Concern-nya FastAPI, bukan Airflow.

Boundary thinking ini inti architecture.

---

### Checkpoint

Coba explain tanpa lihat docs:

1. DAG itu apa?
2. Task itu apa?
3. schedule=None kenapa dipilih?
4. replay_date solve problem apa?
5. Kenapa upstream metadata bisa dipakai hanya sebagai dependency signal?
6. XCom cocok untuk data seperti apa?
7. Kenapa DataFrame besar tetap di Parquet?
8. Kenapa daily replay dan training dipisah?
9. Kenapa registration task terpisah?
10. No-op monitoring run bisa successful kenapa?
11. Apa itu idempotency?
12. Kalau task merah, debugging mulai dari mana?

Kalau bisa jawab dengan reasoning, Airflow section ini sukses.

Next kita pindah ke model serving: gimana champion akhirnya bisa diminta prediction lewat HTTP?
