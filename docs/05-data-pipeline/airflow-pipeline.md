# Airflow Pipeline — Menaruh Manual Steps ke Workflow yang Observable

!!! tip "Praktik Airflow + DVC terbaru"
    Ikuti [panduan workflow dan optimasi](airflow-dvc-workshop.md) untuk dua stage DVC, params.json, pemisahan training/replay, cache features, pool, retry, dan UI tour.


Sekarang manual data pipeline sudah jelas.

Kita tahu input, output, validation, aggregation, feature engineering, dan training.

Baru sekarang orchestration benar-benar meaningful.

Kalau underlying operation belum dipahami, Airflow cuma jadi:

> “UI kotak-kotak yang kalau hijau berarti bagus.”

Kita nggak mau berhenti di situ.

---

## Manual flow vs orchestrated flow

Manual:

~~~text
choose date
↓
simulate_daily_data.py
↓
validate
↓
prepare_daily_demand.py
↓
build_features.py
~~~

Airflow:

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

Task names sengaja dekat dengan business action.

Kenapa?

Karena graph seharusnya bisa dibaca manusia.

---

## Orchestration bukan reimplementation

Bad architecture:

~~~text
manual script
→ implementation A

Airflow DAG
→ copy implementation B

test
→ maybe implementation C
~~~

Sekarang bug fix harus dilakukan tiga tempat.

Project kita pilih:

~~~text
src reusable function
↑             ↑
script       DAG
~~~

Jadi manual dan Airflow share domain logic.

---

## Thin DAG principle

DAG sebaiknya mostly berisi:

- task definition;
- dependency;
- runtime param;
- orchestration behavior.

Bukan hundreds lines Pandas.

Rule:

~~~text
dags
→ when + in what order

src
→ how
~~~

Benefit:

- easier unit testing;
- reusable outside Airflow;
- DAG readable;
- less framework coupling.

---

## Daily DAG step 1 — get_replay_date

Kenapa logical date jadi task/param?

Karena one DAG definition bisa digunakan:

~~~text
Jan 27
Jan 28
Jan 29
~~~

tanpa source edit.

Runtime parameter masuk execution context.

---

## Daily DAG step 2 — release_batch

Wrapper call:

~~~text
release_replay_batch
~~~

Actual work di orchestration module.

Task return small metadata.

Contoh:

~~~text
date
path
status
~~~

Metadata bisa dipakai downstream dan visible di run context.

---

## Dependency without data usage

Interesting pattern:

Downstream task menerima upstream result, tapi kadang isinya tidak dipakai.

Kenapa?

Karena reference itu juga membentuk graph dependency.

Concept:

~~~text
release result object
↓
validate_batch argument
↓
Airflow knows validate depends on release
~~~

Task dependency bisa expressed lewat dataflow syntax walaupun actual data artifact berada di filesystem.

---

## Metadata vs data plane

Ini architecture concept useful.

### Control/metadata plane

~~~text
date
path
row count
run id
status
~~~

### Data plane

~~~text
Parquet
model artifact
large table
~~~

Airflow/XCom cocok buat metadata/control flow.

Storage cocok buat actual large data.

Kalau large data dipaksa lewat XCom, control plane jadi overloaded.

---

## Task boundary = observability boundary

Kenapa validate dan aggregate tidak jadi satu task?

Suppose fail.

Kalau separate:

~~~text
release ✅
validate ❌
aggregate not started
~~~

Kita tahu data quality layer bermasalah.

Kalau combined:

~~~text
process_daily_data ❌
~~~

Root cause kurang narrow.

Task design mempengaruhi operational clarity.

---

## Failure propagation

Default dependency:

~~~text
upstream failed
↓
downstream not executed
~~~

Ini desirable untuk data quality.

Kalau validation gagal, jangan tetap build features dari bad data.

Beberapa production workflow mungkin punya cleanup task yang tetap jalan via custom trigger rule.

Workshop keep default simple.

---

## Retry dan idempotency

Airflow bisa retry task.

Itu hanya aman kalau task tidak menghasilkan duplicate/corrupt state setiap rerun.

Contoh release daily batch:

~~~text
same date
↓
same output path
~~~

lebih predictable daripada append duplicate file.

Orchestration reliability bergantung domain operation reliability.

Airflow tidak magically membuat non-idempotent code aman.

---

## Training DAG

~~~text
create_snapshot
↓
train_model
↓
register_candidate
~~~

### create_snapshot

Run DVC repro.

Kenapa separate task?

Training input jadi explicit lifecycle step.

### train_model

Run baseline + candidate experiment.

Return small summary:

~~~text
run id
MAE
RMSE
beat baseline?
~~~

### register_candidate

Consume training summary.

If candidate kalah baseline:

~~~text
not_registered
~~~

If eligible:

~~~text
challenger
~~~

Ini policy encoded in pipeline.

---

## Why training DAG separate dari daily DAG?

Karena trigger berbeda.

Daily data:

> “New batch arrived.”

Training:

> “We intentionally want new candidate.”

Monitoring:

> “Current model performance suggests retraining.”

Kalau setiap data arrival otomatis train, compute boros dan lifecycle noisy.

Separation DAG = separation business trigger.

---

## Monitoring DAG

~~~text
evaluate_model
↓
maybe_retrain
~~~

maybe_retrain conditional.

Healthy:

~~~text
status = not_needed
~~~

DAG still success.

Ini concept penting:

> Workflow bisa berhasil tanpa menghasilkan model baru.

---

## Initial DVC snapshot vs runtime retraining snapshot

Initial training gunakan DVC stage karena kita ingin source-controlled reproducible snapshot flow.

Runtime retraining membuat newer snapshot berdasarkan logical cutoff lalu log:

~~~text
snapshot name
SHA256
rows
zones
~~~

ke MLflow.

Kenapa Airflow worker tidak auto edit Git/DVC metadata?

Karena runtime pipeline dan source-control workflow punya responsibility berbeda.

Auto commit dari worker bisa introduce:

- credential complexity;
- race conditions;
- dirty repository;
- merge conflict;
- surprising side effect.

Production biasanya gunakan versioned object storage/artifact system untuk runtime dataset lineage.

Workshop memilih simple frozen file + fingerprint.

---

## Scheduling design future

Workshop:

~~~text
schedule=None
~~~

manual trigger.

Production conceptual design:

~~~text
daily data DAG
→ every day after source expected ready

monitoring DAG
→ after ground truth becomes available

training
→ condition-based or manually requested
~~~

Jangan schedule retraining daily hanya karena Airflow bisa.

Schedule harus follow business/data availability.

---

## Backfill

Airflow/data pipeline sering perlu backfill.

Misalnya Jan 29 processing gagal dan baru diperbaiki Feb 2.

Kita mungkin rerun logical Jan 29.

Ini alasan logical date dan idempotency penting.

Processing time:

~~~text
Feb 2
~~~

Data logical time:

~~~text
Jan 29
~~~

Dua waktu beda.

---

## Catchup

DAG config workshop:

~~~text
catchup=False
~~~

Kenapa?

Kita tidak ingin Airflow otomatis generate historical scheduled runs dari start_date sampai sekarang.

Historical replay kita control lewat param.

Kalau catchup aktif dengan daily schedule dari 2025, workshop bisa tiba-tiba punya ratusan runs.

---

## start_date bukan berarti langsung run

Airflow start_date sering disalahpahami.

Dia mendefinisikan scheduling boundary, bukan “jalankan DAG saat Python file dibaca.”

Workshop manual schedule membuat ini lebih simple, tapi concept tetap useful.

---

## Parameter experiment

Monitoring DAG expose:

~~~text
degradation_multiplier
min_samples
recent_limit
~~~

Parameter ini memungkinkan workshop explore policy tanpa source edit.

Namun production parameter changes sebaiknya governed.

UI flexibility bukan excuse buat random threshold production.

---

## Airflow logs vs application logs

Task log capture execution output/error.

FastAPI punya service logs.

MLflow punya run metadata.

Grafana punya metrics.

Observability source berbeda-beda.

Kalau training task fail karena MLflow unavailable, Airflow log mungkin menunjukkan connection error.

Root cause tetap external dependency.

---

## Orchestrator boundary

Airflow sebaiknya tidak menjadi:

- data warehouse;
- model registry;
- large artifact store;
- business API;
- source control.

Dia coordinate systems.

Architecture sehat membiarkan masing-masing tool fokus responsibility.

---

## Failure scenario exercise

Suppose:

~~~text
release_batch ✅
validate_batch ✅
aggregate_demand ❌
~~~

Pertanyaan:

1. Apakah rebuild_features jalan?
2. Raw batch perlu direlease ulang?
3. Di mana root cause kemungkinan?
4. Setelah bug aggregation fix, apakah rerun whole DAG aman?

Jawaban tergantung task retry/idempotency, tapi graph memberi clarity.

---

## Another scenario

~~~text
train_model ✅
register_candidate ❌
~~~

Apakah perlu train ulang model?

Belum tentu.

Training result/MLflow run mungkin sudah valid.

Problem bisa hanya Registry connectivity.

Task boundary membantu recovery lebih surgical.

---

## Checkpoint

1. Manual script dan Airflow task relationship apa?
2. Kenapa DAG tipis?
3. Metadata plane vs data plane?
4. Task boundary membantu observability bagaimana?
5. Dependency bisa terbentuk walau upstream value tidak dibaca bagaimana?
6. Retry relation ke idempotency?
7. Daily, training, monitoring DAG kenapa dipisah?
8. Runtime retraining kenapa tidak auto Git commit?
9. schedule dan data availability harus relate bagaimana?
10. Apa itu backfill?
11. processing time beda apa dengan logical data time?
12. catchup=False menghindari apa di workshop?
13. Kalau train success tapi registration fail, kenapa tidak selalu perlu retrain?

Kalau ini clear, kalian ngerti Airflow sebagai workflow control plane, bukan sekadar scheduler script.
