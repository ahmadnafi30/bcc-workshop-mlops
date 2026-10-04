# BCC Workshop — MLOps

End-to-end MLOps workshop project using an urban mobility / taxi demand forecasting use case.

Project ini ngebahas lifecycle ML dari data ingestion, feature engineering, experiment tracking, model registry, serving, CI/CD, monitoring, sampai retraining.

## Stack

- Python
- uv
- Airflow
- DVC
- MLflow
- FastAPI
- Docker / Docker Compose
- GitHub Actions
- Prometheus
- Grafana

## Quick Start

Project ini pakai **uv** buat Python environment dan dependency management.

Dari root repository:

```bash
uv sync
```

Karena project punya `.python-version`, uv bakal pakai Python 3.11 untuk environment workshop.

Jalankan command project lewat `uv run`:

```bash
uv run pytest
uv run python scripts/bootstrap_data.py
uv run dvc repro create_training_snapshot
```

Kalau mau menjalankan Airflow orchestration:

```bash
uv sync --group airflow
uv run --group airflow python scripts/start_airflow.py
```

DAG utama yang tersedia:

```text
taxi_daily_replay
taxi_initial_training
```

Setelah model sudah dipromote ke alias `champion`, start serving API:

```bash
uv run uvicorn api.main:app --reload
```

Endpoint utama:

```text
GET  /health
GET  /model-info
POST /predict
```

Interactive API docs tersedia di:

```text
http://127.0.0.1:8000/docs
```

Kalau mau jalanin local stack pakai Docker:

```bash
docker compose up -d --build
```

Service yang langsung hidup:

```text
MLflow  -> http://localhost:5000
Airflow -> http://localhost:8080
FastAPI -> http://localhost:8000
```

Untuk bootstrap data lewat container:

```bash
docker compose run --rm workspace python scripts/bootstrap_data.py
docker compose run --rm workspace python scripts/prepare_historical_demand.py
docker compose run --rm workspace python scripts/build_features.py
```

GitHub Actions sekarang punya dua workflow:

```text
CI
→ tests + Docker build validation

Container Delivery
→ publish api / mlflow / airflow image ke GHCR setelah CI main sukses
```

Jadi CD project ini berhenti di **container delivery**, belum auto-deploy ke server/cloud.

Kalau mau masuk ke virtual environment secara manual, uv tetap bikin environment di `.venv/`.

> `uv.lock` akan dibuat atau di-update oleh uv saat dependency resolution dijalankan. Setelah environment sudah diverifikasi di mesin workshop, lock file itu sebaiknya ikut di-commit supaya install peserta benar-benar reproducible.

## Documentation

Workshop materials dan hands-on guide ada di `docs/`.

## High-level Flow

```text
Data
  ↓
Airflow
  ↓
DVC snapshot
  ↓
Training
  ↓
MLflow
  ↓
FastAPI
  ↓
Docker
  ↓
GitHub Actions
  ↓
Monitoring
  ↓
Retraining
```
