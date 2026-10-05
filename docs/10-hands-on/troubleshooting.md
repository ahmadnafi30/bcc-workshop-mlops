# Troubleshooting — Jangan Debug Seluruh MLOps Stack Sekaligus

Kalau system banyak komponen, instinct beginner sering:

> “Semuanya error.”

Padahal debugging lebih efektif kalau kita identify **boundary paling kecil yang fail**.

Use checklist ini from bottom to top.

---

## 1. Setup layer

### uv command not found

uv belum installed / PATH belum update.

### Wrong Python

~~~bash
uv run python --version
~~~

Expected 3.11.x.

### Module missing

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

## 2. Data layer

### TLC base URL AccessDenied

Normal kalau buka directory prefix.

Use bootstrap script.

### Historical file missing

Check exact date under data folders.

### Feature build fail

Check processed demand completeness.

---

## 3. Model layer

### Snapshot missing

Run DVC repro or manual snapshot creation.

### Model worse than baseline

Not infrastructure bug.

Inspect ML/features/model.

Do not manipulate metric.

---

## 4. MLflow layer

### UI unreachable

Is start_mlflow process running?

Port 5000 free?

### Registry empty after Docker transition

Workshop local + Docker should share .mlflow.

Pastikan kalian pakai helper project dan Compose current config.

### Champion missing

Promote registered version.

---

## 5. Airflow layer

### DAG missing

~~~bash
uv run --group airflow airflow dags list
~~~

Missing DAG usually parse/import error.

### Task failed

Open task log.

Ask:

~~~text
input exists?
service reachable?
exception?
upstream output?
~~~

---

## 6. API layer

### Connection refused

FastAPI process/container not listening.

### /health 200, /model-info 503

API alive, model dependency unavailable.

### /predict 422

Semantic input/history issue.

Check target time and 168h history.

---

## 7. Docker layer

### Port already in use

Stop local process.

### API cannot reach MLflow

Check MLFLOW_TRACKING_URI.

Inside Compose should point service hostname.

### Data missing inside container

Check bind mount.

---

## 8. Monitoring layer

### Prometheus target DOWN

Open:

~~~text
http://localhost:9090/targets
~~~

Check API metrics reachable.

### Grafana empty

Debug chain:

~~~text
traffic?
↓
API metric?
↓
Prometheus scrape?
↓
query?
↓
Grafana datasource?
~~~

### MAE panel empty

Need:

~~~text
prediction log
+
ground truth
+
evaluate_predictions
~~~

---

## 9. CI layer

### Branch policy fail

Check PR direction.

### Ruff fail

Read exact file/line.

### Docker build fail

Python tests green does not imply image build green.

Read build logs.

---

## Golden rule

Jangan random restart semua service setiap error.

Itu bisa hide root cause.

Tanya:

> “Apa boundary pertama yang menghasilkan output yang salah?”

Then debug there.

MLOps stack besar jadi manageable kalau kalian treat sebagai chain of smaller systems.
