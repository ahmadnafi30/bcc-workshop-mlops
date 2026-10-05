# Troubleshooting — Jangan Debug “Seluruh MLOps” Sekaligus

Kalau whole system fail, reaction pertama sering:

> “Waduh semuanya rusak.”

Padahal biasanya satu boundary saja.

Mindset debugging kita:

~~~text
Find the smallest failing layer.
~~~

---

# 1. Setup / Python

## uv not found

uv belum installed / PATH belum update.

Restart terminal setelah install kalau perlu.

## Wrong Python

~~~bash
uv run python --version
~~~

Expected 3.11.x.

## Module missing

~~~bash
uv sync
~~~

Airflow:

~~~bash
uv sync --group airflow
~~~

Docs:

~~~bash
uv sync --group docs
~~~

---

# 2. Data

## TLC URL AccessDenied

Kalau yang dibuka directory base URL, expected.

Gunakan bootstrap script.

## Bootstrap download slow

Monthly source besar.

Presenter sebaiknya pre-download.

## Processed daily file missing

Check:

~~~text
raw daily released?
date correct?
prepare daily demand run?
~~~

---

# 3. Features

## Feature rows empty

Possible:

- insufficient history,
- wrong date range,
- lag_168h warm-up not complete.

## Metric suspiciously amazing

Check leakage.

Particularly rolling calculation and target inclusion.

---

# 4. DVC

## Snapshot missing

~~~bash
uv run dvc repro create_training_snapshot
~~~

Check feature dependency exists.

## DVC says changed

Inspect which dependency changed.

Jangan langsung delete cache.

---

# 5. MLflow

## UI empty

Check tracking server yang sama.

Use:

~~~bash
uv run python scripts/start_mlflow.py
~~~

## Model disappeared after Docker

Local and Compose should share .mlflow.

Pastikan earlier run juga use helper/state path itu.

## Register fails

Run ID valid?

Model artifact exists?

---

# 6. Airflow

## DAG missing

~~~bash
uv run --group airflow airflow dags list
~~~

Check parse/import error.

## One task fail

Open exact task log.

Do not restart everything first.

Ask:

- input file?
- param?
- dependency service?
- exception?

## Airflow port conflict

Local process / Docker Airflow mungkin sama-sama start.

Stop salah satu.

---

# 7. FastAPI

## connection refused

Uvicorn/API container not running.

## /health 200 but /model-info 503

API okay.

MLflow/champion problem.

## /predict 422

Check:

- exact hour?
- zone valid?
- history complete?
- processed daily files exist?

---

# 8. Docker

## port already in use

Check services yang sedang pakai:

~~~text
3000
5000
8000
8080
9090
~~~

Stop local process.

## container unhealthy

~~~bash
docker compose ps
docker compose logs <service>
~~~

## build slow

First build Airflow especially memang heavy.

---

# 9. Prometheus

## target DOWN

Open:

~~~text
http://localhost:9090/targets
~~~

Prometheus internal target harus:

~~~text
api:8000
~~~

not localhost.

## metric missing

Check /metrics first.

Kalau source endpoint belum punya metric, Grafana obviously nggak bisa show.

---

# 10. Grafana

## dashboard empty

Debug chain:

~~~text
API traffic generated?
↓
/metrics contains values?
↓
Prometheus target UP?
↓
PromQL returns data?
↓
Grafana datasource healthy?
↓
panel query?
~~~

Jangan edit dashboard dulu kalau Prometheus query kosong.

---

# 11. CI

## Ruff fail

Read exact file + line.

Usually simple style/import issue.

## pytest fail

Open traceback.

Identify test domain.

## docs strict fail

Likely nav/reference/warning.

## branch policy fail

Correct flow:

~~~text
feat/fix/docs/chore
→ develop

develop
→ main
~~~

---

# 12. Monitoring / retraining

## evaluation_count = 0

Ground truth for logged predictions belum available / target date processed data missing.

## retrain false

Could be healthy model.

Not a bug.

## retrain expected but not happening

Check:

- sample count >= min?
- recent MAE > threshold?
- champion reference MAE available?
- logs use champion model version?

---

# Golden debugging rule

Jangan tanya:

> “Kenapa MLOps saya error?”

Tanya:

> “Kenapa task aggregate_demand untuk Jan 28 tidak menemukan expected input file?”

Semakin specific pertanyaannya, semakin cepat fix-nya.
