# BCC Workshop — MLOps

Hi peers 👋

Welcome to **BCC Workshop — MLOps**, a beginner-friendly end-to-end project where we learn how a machine learning model moves from a notebook idea into a small production-like system.

The use case is **NYC Yellow Taxi Demand Forecasting**: predicting how many taxi pickups will happen in each Manhattan taxi zone one hour ahead.

This workshop is presented by:

- **Ahmad Nafi Mubarok**
- **Fatoni Murfid Syafii**

> The goal is not to build the fanciest forecasting model. The goal is to understand the ML lifecycle around the model: data, reproducibility, tracking, serving, automation, delivery, monitoring, and retraining.

## What are we building?

~~~text
NYC TLC data
    ↓
data preparation
    ↓
feature engineering
    ↓
DVC training snapshot
    ↓
model training
    ↓
MLflow experiment tracking
    ↓
MLflow Model Registry
    ↓
Airflow orchestration
    ↓
FastAPI serving
    ↓
Docker / Docker Compose
    ↓
GitHub Actions CI/CD
    ↓
Prometheus + Grafana
    ↓
performance monitoring
    ↓
retraining → challenger model
~~~

Every tool enters the story because we already have a problem it solves.

## Workshop stack

| Area | Tool |
| --- | --- |
| Python environment | uv |
| ML model | scikit-learn |
| Data versioning | DVC |
| Workflow orchestration | Apache Airflow |
| Experiment tracking | MLflow |
| Model registry | MLflow Model Registry |
| Model API | FastAPI + Uvicorn |
| Containerization | Docker |
| Local multi-service stack | Docker Compose |
| CI/CD | GitHub Actions + GHCR |
| Metrics | Prometheus |
| Dashboard | Grafana |

## Quick start

### 1. Clone

~~~bash
git clone https://github.com/ahmadnafi30/bcc-workshop-mlops.git
cd bcc-workshop-mlops
~~~

### 2. Install

This project uses Python 3.11 and uv.

~~~bash
uv sync
~~~

Run tests:

~~~bash
uv run pytest
~~~

### 3. Open the learning material

~~~bash
uv sync --group docs
uv run --group docs mkdocs serve
~~~

Open:

~~~text
http://127.0.0.1:8000
~~~

If you are new to MLOps, start with the docs instead of jumping directly into Docker or Airflow.

## Local service stack

Later in the workshop:

~~~bash
docker compose up -d --build
~~~

| Service | URL |
| --- | --- |
| MLflow | http://localhost:5000 |
| Airflow | http://localhost:8080 |
| FastAPI | http://localhost:8000 |
| FastAPI docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

## Repository map

~~~text
.
├── api/                 # HTTP layer for model serving
├── dags/                # Airflow DAG definitions
├── data/                # local generated data
├── docker/              # container image definition
├── docs/                # workshop material
├── monitoring/          # Prometheus + Grafana config
├── notebooks/           # lightweight data exploration
├── scripts/             # human-friendly commands
├── src/                 # reusable project logic
├── tests/               # automated tests
├── docker-compose.yml
├── dvc.yaml
├── mkdocs.yml
└── pyproject.toml
~~~

Useful rule:

~~~text
scripts/ = "run this manually"
src/     = "reusable logic"
dags/    = "when + in what order"
api/     = "expose predictions through HTTP"
~~~

## Git workflow

~~~text
feat/* or fix/*
        ↓
      develop
        ↓
       main
~~~

- **main**: stable workshop release
- **develop**: integration branch
- **feat/***: new feature work
- **fix/***: bug fixes
- **docs/***: documentation-only changes

Read CONTRIBUTING.md before creating a PR.

## Dataset note

The project uses official NYC Taxi & Limousine Commission Yellow Taxi Trip Records.

Opening the CloudFront directory URL itself can show **AccessDenied**. That is expected because directory listing is not public. We access exact monthly Parquet objects instead, such as:

~~~text
.../yellow_tripdata_2025-01.parquet
~~~

The bootstrap script handles those paths for you.

## Core learning path

~~~text
Setup
  ↓
Data
  ↓
Baseline
  ↓
DVC
  ↓
MLflow
  ↓
Airflow
  ↓
FastAPI
  ↓
Docker
  ↓
CI/CD
  ↓
Monitoring
  ↓
Retraining
~~~

## Production-like, not production-copy-paste

This repository deliberately simplifies a few things:

- local filesystem instead of cloud object storage,
- SQLite for local MLflow metadata,
- Airflow standalone,
- historical replay instead of waiting for real future data,
- manual champion promotion,
- no Kubernetes.

The concepts transfer. The infrastructure can grow later.
