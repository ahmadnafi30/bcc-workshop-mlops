# Docker

Sebelum Docker masuk, semua service sebenarnya sudah bisa jalan langsung dari uv environment.

Masalah berikutnya:

> gimana caranya supaya environment serving, tracking, dan orchestration konsisten di laptop yang berbeda?

Di sini Docker mulai kepake.

## Satu Dockerfile, beberapa target

Project punya:

```text
docker/Dockerfile
```

tapi image-nya nggak cuma satu bentuk.

Kita pakai multi-stage build:

```text
base
├── api
├── mlflow
└── airflow
```

### base

Isinya dependency core project:

```text
Python 3.11
uv
DVC
MLflow client
FastAPI
scikit-learn
project package
```

Target ini juga dipakai service `workspace` buat command one-shot seperti bootstrap data.

### api

Reuse `base`, lalu start:

```text
uvicorn api.main:app
```

### mlflow

Reuse `base`, lalu start MLflow Tracking Server.

Metadata disimpan ke SQLite di volume Docker:

```text
/mlflow/mlflow.db
```

Artifact juga disimpan persisten:

```text
/mlflow/artifacts
```

MLflow serve artifacts lewat tracking server, jadi FastAPI dan Airflow cukup tahu:

```text
http://mlflow:5000
```

Mereka nggak perlu mount folder artifact MLflow langsung.

### airflow

Reuse `base`, lalu install dependency group tambahan:

```text
airflow
```

Setelah itu image membawa folder `dags/` dan jalan lewat:

```text
python scripts/start_airflow.py
```

## Build manual

Kalau mau lihat target satu-satu:

```bash
docker build -f docker/Dockerfile --target api -t bcc-mlops-api .
docker build -f docker/Dockerfile --target mlflow -t bcc-mlops-mlflow .
docker build -f docker/Dockerfile --target airflow -t bcc-mlops-airflow .
```

Tapi untuk workshop kita lebih sering pakai Docker Compose karena service ini memang saling berhubungan.

## Kenapa nggak satu container?

Secara teknis bisa saja.

Tapi kalau semua dimasukin ke satu container:

```text
FastAPI + MLflow + Airflow
```

boundary service jadi kabur.

Dengan container terpisah, lebih gampang lihat:

```text
API punya lifecycle sendiri
MLflow punya storage sendiri
Airflow punya state sendiri
```

Ini juga lebih dekat dengan cara service beneran dideploy.

## Non-root user

Image jalan sebagai user `app`, bukan root.

UID-nya dibuat 1000 supaya bind-mounted data di Linux lebih nyaman dan file output nggak selalu jadi milik root.

Ini bukan security hardening production lengkap, tapi sudah lebih baik daripada semua process jalan sebagai root.
