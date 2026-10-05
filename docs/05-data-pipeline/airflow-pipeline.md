# Data Pipeline — Airflow Orchestration: Menaruh Manual Steps ke Workflow yang Observable

Sekarang kita punya manual data pipeline yang sudah jelas.

Baru sekarang kita orchestrate.

Ini urutan belajar yang sengaja dipilih.

Kalau underlying command belum dipahami, Airflow UI jadi magic box.

---

## Daily DAG mapping

Manual conceptual flow:

~~~text
choose date
↓
release daily data
↓
validate
↓
aggregate
↓
build features
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

One-to-one enough buat gampang trace.

---

## Task boundaries

Kenapa validate separate dari aggregate?

Kalau validation fail, kita tahu data quality problem.

Kalau digabung:

~~~text
validate + aggregate
~~~

error location less clear.

Task boundary adalah observability decision juga.

---

## Metadata passing

Release task return:

~~~text
date
path
rows
~~~

Downstream use metadata.

Large data tetap di Parquet.

Kenapa?

Workflow engine coordinate.

Storage stores data.

Jangan campur responsibility.

---

## Training DAG

~~~text
create_snapshot
↓
train_model
↓
register_candidate
~~~

Snapshot task separate supaya training input explicit.

Training return metrics/run IDs small enough buat task metadata.

Registration consume result.

---

## Monitoring DAG

~~~text
evaluate_model
↓
maybe_retrain
~~~

maybe_retrain conditional.

Kalau no retrain:

~~~text
status = not_needed
~~~

This is expected success.

---

## Runtime retraining snapshot vs DVC stage

Initial snapshot punya DVC reproducibility flow.

Runtime Airflow retraining create newer snapshot and log fingerprint to MLflow.

Kenapa Airflow nggak otomatis dvc add + commit repository?

Karena runtime pipeline modifying source repository metadata is different concern and can create race/permission complexity.

Workshop keep runtime lineage via snapshot name + SHA in MLflow.

Ini intentional simplification.

---

## Retry

Airflow can retry task.

Makanya task harus idempotent.

Kalau retry release_batch produce duplicate data, orchestration reliability rusak.

---

## Scheduling future extension

Workshop manual.

Production design bisa:

~~~text
daily data DAG
→ every day

monitoring DAG
→ after ground truth available

training
→ condition triggered
~~~

Jangan schedule retraining blindly kalau business logic condition-based.

---

## Failure propagation

Upstream fail biasanya downstream blocked.

Ini good.

Bad input tidak lanjut.

But sometimes cleanup task might need trigger rule different.

Workshop keep default dependency simple.

---

## Checkpoint

1. Manual script dan Airflow task relationship?
2. Task boundary bantu observability bagaimana?
3. Metadata vs large data?
4. Kenapa runtime Airflow nggak commit DVC metadata?
5. Retry relation ke idempotency?
