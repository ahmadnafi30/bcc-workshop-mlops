# Glossary — Istilah yang Sering Muncul

Halaman ini buat quick reference.

Kalau di tengah workshop ada istilah yang lupa, nggak perlu malu. MLOps memang banyak terminology.

---

## Artifact

Output yang disimpan untuk dipakai atau diaudit nanti.

Contoh:

- trained model,
- metrics JSON,
- Docker image,
- evaluation Parquet.

---

## Baseline

Metode sederhana yang jadi pembanding.

Project kita:

~~~text
prediction(t)
=
demand(t - 24h)
~~~

Model ML harus justify complexity dengan beat baseline.

---

## Champion

Alias di Model Registry untuk model yang sekarang approved buat serving.

~~~text
champion
→ version 3
~~~

---

## Challenger

Candidate model yang sedang dipertimbangkan untuk replace champion.

Belum automatically production.

---

## CI

Continuous Integration.

Automated checks saat source changes.

Project kita check:

- lint,
- tests,
- docs,
- Docker builds.

---

## CD

Bisa berarti Continuous Delivery atau Continuous Deployment.

Project kita pakai **Continuous Delivery**:

~~~text
main CI success
↓
publish container to GHCR
~~~

Belum auto-deploy ke cloud/server.

---

## Container

Running instance dari Docker image.

~~~text
image
→ template

container
→ running instance
~~~

---

## DAG

Directed Acyclic Graph.

Airflow workflow representation.

~~~text
task A
↓
task B
↓
task C
~~~

Directed = dependency punya arah.

Acyclic = tidak ada circular dependency.

---

## Data leakage

Feature memakai information yang belum seharusnya available saat prediction.

Contoh buruk:

~~~text
predict 18:00
but feature includes actual 18:00 demand
~~~

Metric bisa terlihat bagus tapi fake.

---

## DVC

Data Version Control.

Di project ini dipakai untuk training snapshot pipeline reproducibility.

Bukan replacement Git dan bukan experiment tracker.

---

## Feature

Input untuk model.

Contoh:

~~~text
hour
lag_24h
rolling_mean_3h
~~~

---

## Ground truth

Actual outcome yang dipakai buat evaluate previous prediction.

Prediction 18:00 dibanding actual 18:00 setelah hour selesai.

---

## Histogram

Prometheus metric type untuk distribution observation.

Kita pakai buat API latency.

---

## Idempotency

Rerun logical operation yang sama tidak menghasilkan unintended duplicate/corruption.

Useful untuk pipeline retry/backfill.

---

## Image

Built Docker artifact/template.

Container dibuat dari image.

---

## Inference

Proses menggunakan trained model untuk menghasilkan prediction.

---

## Lag feature

Historical value pada offset tertentu.

~~~text
lag_1h
→ 1 hour before

lag_24h
→ same hour yesterday
~~~

---

## Lineage

Trace dari output ke origin.

Contoh:

~~~text
prediction
↓
model version
↓
MLflow run
↓
dataset SHA
~~~

---

## MAE

Mean Absolute Error.

Average absolute prediction error.

Kalau MAE 10:

> Rata-rata prediction meleset sekitar 10 target units.

---

## MLflow Run

Satu execution experiment yang punya:

- params,
- metrics,
- tags,
- artifacts,
- unique run ID.

---

## Model Registry

Versioned catalog untuk model artifacts setelah experiment.

Kita punya version + aliases.

---

## Orchestration

Mengatur:

- step,
- dependency,
- schedule,
- execution state.

Airflow adalah orchestrator kita.

---

## Prometheus Scrape

Prometheus melakukan HTTP request ke metrics endpoint untuk collect current values.

~~~text
Prometheus
→ GET /metrics
~~~

---

## RMSE

Root Mean Squared Error.

Regression metric yang memberi penalty lebih besar ke large errors.

---

## Rolling Feature

Statistic dari recent historical window.

Contoh:

~~~text
rolling_mean_3h
~~~

average demand 3 completed hours sebelumnya.

---

## Serving

Membuat inference available melalui stable interface.

Project kita pakai FastAPI HTTP.

---

## Snapshot

Frozen dataset state untuk satu training cycle.

~~~text
taxi_demand_2025-01-26.parquet
~~~

---

## Task

Unit of work dalam Airflow DAG.

Contoh:

~~~text
validate_batch
~~~

---

## Training-serving consistency

Feature meaning saat training harus sama dengan saat serving.

Kalau lag_24h semantics beda antara offline dan API, model quality bisa rusak.

---

## Volume

Storage yang dipakai container dan punya lifecycle terpisah dari container process.

Bisa Docker named volume atau bind mount depending context.

---

## XCom

Airflow mechanism untuk passing small task metadata/result.

Good:

~~~text
date
path
row count
run ID
~~~

Bad:

~~~text
huge DataFrame
~~~

Large data lebih baik lewat file/object storage.
