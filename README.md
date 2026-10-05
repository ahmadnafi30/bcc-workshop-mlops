# BCC Workshop — MLOps

Hi peers 👋

Welcome to **BCC Workshop — MLOps**.

Repo ini bukan sekadar kumpulan contoh Docker, Airflow, atau MLflow. Kita pakai satu use case yang sama dari awal sampai akhir supaya kalian bisa lihat **gimana sebuah Machine Learning model pelan-pelan berubah dari experiment biasa menjadi production-like ML system**.

Use case kita:

> **NYC Yellow Taxi Demand Forecasting — predict berapa banyak pickup taxi yang akan terjadi di setiap Manhattan taxi zone satu jam ke depan.**

Workshop ini dibawakan oleh:

- **Ahmad Nafi Mubarok**
- **Fatoni Murfid Syafii**

Kalau kalian baru pertama kali dengar istilah seperti DAG, DVC, Model Registry, champion, XCom, Prometheus scrape, atau retraining trigger, santai aja. Docs di repo ini memang sengaja ditulis untuk audience yang **sudah tahu basic Python/ML, tapi masih newbie di MLOps**.

---

## Kenapa repo ini ada?

Coba bayangin kalian sudah punya model:

~~~text
Validation MAE = 10.2
model.joblib
~~~

Terus ada yang nanya:

> Dataset exact yang dipakai model ini mana?

> Hyperparameter-nya apa?

> Bisa dipakai backend nggak?

> Kalau modelnya memburuk bulan depan kita tahu dari mana?

> Siapa yang retrain?

> Model version mana yang sekarang live?

Nah, mulai dari situ kita sudah masuk problem yang lebih besar dari sekadar training model.

Repo ini membangun lifecycle:

~~~text
NYC TLC Data
    ↓
Data Preparation
    ↓
Feature Engineering
    ↓
Training Snapshot
    ↓
DVC
    ↓
Model Training
    ↓
MLflow Tracking
    ↓
Model Registry
    ↓
Airflow Orchestration
    ↓
FastAPI Serving
    ↓
Docker / Docker Compose
    ↓
GitHub Actions CI/CD
    ↓
Prometheus + Grafana
    ↓
Model Performance Monitoring
    ↓
Retraining
    ↓
Challenger
    ↓
Review / Promotion
    ↓
Champion
~~~

Jangan hafalin diagram-nya.

Pertanyaan utama workshop ini selalu:

> **“Problem apa yang lagi kita solve?”**

---

## Workshop stack

| Area | Tool |
| --- | --- |
| Python project environment | uv |
| Machine Learning | scikit-learn |
| Data snapshot reproducibility | DVC |
| Workflow orchestration | Apache Airflow |
| Experiment tracking | MLflow |
| Model lifecycle | MLflow Model Registry |
| Model serving | FastAPI + Uvicorn |
| Runtime packaging | Docker |
| Local multi-service environment | Docker Compose |
| Repository automation | GitHub Actions |
| Container registry | GHCR |
| Metrics collection | Prometheus |
| Dashboard | Grafana |

Tools-nya memang lumayan banyak, tapi setiap tool baru masuk setelah kita punya alasan kenapa dia dibutuhkan.

---

## Quick start

### 1. Clone

~~~bash
git clone https://github.com/ahmadnafi30/bcc-workshop-mlops.git
cd bcc-workshop-mlops
~~~

### 2. Setup Python environment

Project pakai **Python 3.11** dan **uv**.

~~~bash
uv sync
~~~

Cek:

~~~bash
uv run python --version
uv run python scripts/doctor.py
~~~

### 3. Run tests

~~~bash
uv run pytest
~~~

Kalau fresh clone sudah green, kita punya starting point yang jelas.

### 4. Buka docs

~~~bash
uv sync --group docs
uv run --group docs mkdocs serve
~~~

Open:

~~~text
http://127.0.0.1:8000
~~~

Kalau kalian masih newbie di MLOps, **recommended banget mulai dari docs**, jangan langsung lompat ke docker compose up.

---

## Learning path

~~~text
Step 0
Setup

Step 1
Data

Step 2
Features + Baseline Model

Step 3
DVC

Step 4
MLflow

Step 5
Airflow

Step 6
FastAPI

Step 7
Docker

Step 8
CI/CD

Step 9
Monitoring

Step 10
Retraining
~~~

Hands-on dibuat berurutan supaya tool berikutnya selalu menjawab problem dari step sebelumnya.

---

## Repository structure

~~~text
.
├── api/                 # HTTP layer
├── dags/                # Airflow DAG definitions
├── data/                # generated local data
├── docker/              # Dockerfile
├── docs/                # workshop material
├── monitoring/          # Prometheus + Grafana config
├── notebooks/           # lightweight EDA
├── scripts/             # commands humans run
├── src/                 # reusable business logic
├── tests/               # automated tests
├── docker-compose.yml
├── dvc.yaml
├── mkdocs.yml
└── pyproject.toml
~~~

Rule yang enak diingat:

~~~text
src/
→ HOW

scripts/
→ RUN THIS MANUALLY

dags/
→ WHEN + IN WHAT ORDER

api/
→ HOW OTHER SYSTEMS ACCESS THE MODEL
~~~

---

## Local service stack

Setelah model champion sudah ada dan kita masuk container section:

~~~bash
docker compose up -d --build
~~~

Service:

| Service | URL |
| --- | --- |
| MLflow | http://localhost:5000 |
| Airflow | http://localhost:8080 |
| FastAPI | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

---

## Git workflow

Kita pakai:

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

- **main** = stable workshop release
- **develop** = integration branch
- **feat/*** = feature
- **fix/*** = bug fix
- **docs/*** = docs-only changes
- **chore/*** = maintenance

Jadi feature baru tidak langsung ke main.

Detail-nya ada di CONTRIBUTING.md dan section Git Workflow.

---

## Tentang data NYC TLC

Official Yellow Taxi monthly data diakses sebagai exact Parquet object.

Kalau kalian buka base CloudFront folder dan dapat:

~~~text
AccessDenied
~~~

itu bukan berarti datanya unavailable.

Directory listing memang tidak public.

Bootstrap script tahu exact monthly object path.

---

## Production-like, bukan production copy-paste

Repo ini deliberately simplify beberapa hal:

- local filesystem,
- SQLite MLflow metadata,
- Airflow standalone,
- Docker Compose,
- historical replay,
- manual champion approval.

Kenapa?

Karena kita ingin ngerti lifecycle dulu.

Production besar mungkin pakai:

- S3,
- Kubernetes,
- managed Airflow,
- external database,
- feature store,
- more advanced monitoring.

Concept-nya tetap transferable.

---

## Satu kalimat yang paling penting

> **Jangan mulai dari tool. Mulai dari problem.**

Kita nggak pakai Airflow karena “MLOps harus ada Airflow”.

Kita pakai Airflow karena manual workflow mulai susah dikoordinasikan.

Kita nggak pakai MLflow karena UI-nya keren.

Kita pakai MLflow karena experiment history mulai susah dilacak.

Kalau mindset ini kebawa setelah workshop, kalian sudah dapat salah satu bagian paling penting dari MLOps.
