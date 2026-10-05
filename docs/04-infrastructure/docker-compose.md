# Docker Compose — Running the Whole Local Stack

## Setelah Docker, problem berikutnya adalah jumlah service

Kita punya:

~~~text
MLflow
FastAPI
Airflow
Prometheus
Grafana
~~~

Kalau semuanya dijalankan manual dengan docker run, kita harus define network, port, volume, env var, dan dependency satu-satu.

Docker Compose bantu describe local stack dalam satu file.

---

# docker-compose.yml

File:

~~~text
docker-compose.yml
~~~

Isi utamanya:

~~~text
services
volumes
ports
environment
depends_on
healthcheck
~~~

---

# Service kita

## mlflow

Port 5000.

Experiment tracking + Registry.

## api

Port 8000.

Prediction API + metrics.

## airflow

Port 8080.

Orchestration UI.

## prometheus

Port 9090.

Scrape/store time-series metrics.

## grafana

Port 3000.

Visualization.

---

# Start stack

~~~bash
docker compose up -d --build
~~~

## up

Create/start services.

## -d

Detached mode.

## --build

Build image dulu kalau dibutuhkan.

---

# Internal networking

Compose creates a shared network.

Service names jadi DNS.

~~~text
api → mlflow:5000
prometheus → api:8000
grafana → prometheus:9090
~~~

Dari browser host tetap pakai localhost + published port.

---

# depends_on dan healthcheck

Container started belum tentu service ready.

MLflow process bisa baru startup tapi belum ready accept HTTP request.

Healthcheck memberi signal readiness.

API depends on MLflow healthy.

Ini lebih baik daripada cuma berharap startup timing selalu sama.

---

# Shared data

Host:

~~~text
./data
~~~

mounted ke:

~~~text
/app/data
~~~

di service yang butuh.

Flow:

~~~text
Airflow writes processed demand
↓
host file updated
↓
FastAPI can read same file
~~~

Untuk workshop, transparent filesystem sharing ini enak dipahami.

---

# MLflow state

~~~text
./.mlflow
→ /mlflow
~~~

Local helper start_mlflow.py dan Compose MLflow pakai folder sama.

Jadi participant bisa belajar MLflow local dulu, lalu pindah Compose tanpa empty registry baru.

---

# Named volumes

~~~text
airflow-home
prometheus-data
grafana-data
dvc-cache
~~~

Lifecycle state terpisah dari container process.

Container bisa recreated tanpa otomatis menghapus named volume.

---

# workspace service

Workspace adalah one-shot tools container.

Contoh:

~~~bash
docker compose run --rm workspace   python scripts/doctor.py
~~~

Dia pakai project environment tapi tidak jalan terus.

---

# Cek status

~~~bash
docker compose ps
~~~

Lihat:

- running,
- health,
- ports.

Ini salah satu first debugging command.

---

# Logs

~~~bash
docker compose logs -f
~~~

atau:

~~~bash
docker compose logs -f api
~~~

Narrow service kalau bisa.

---

# Stop stack

~~~bash
docker compose down
~~~

Named volumes tetap.

---

# Reset named volumes

~~~bash
docker compose down -v
~~~

Hati-hati, state Airflow/Prometheus/Grafana reset.

Tapi .mlflow adalah bind-mounted host folder, jadi tidak ikut hilang hanya karena down -v.

---

# Production note

Compose sangat cocok untuk local integration/workshop.

Production besar bisa pindah ke platform lain.

Yang transferable adalah:

- service boundary,
- network addressing,
- persistent storage,
- health/readiness,
- environment configuration.

Bukan necessarily Compose tool-nya sendiri.

---

# Tiga hal yang harus clear

~~~text
1. localhost di container
   bukan container lain

2. service name
   jadi internal DNS

3. container lifecycle
   beda dengan persistent storage lifecycle
~~~

Kalau tiga ini clear, sebagian besar confusion Compose beginner sudah lewat.
