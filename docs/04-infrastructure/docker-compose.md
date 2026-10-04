# Docker Compose

Docker Compose dipakai buat nyalain local MLOps stack tanpa buka tiga terminal dan setup environment service satu-satu.

Architecture-nya:

```text
                     Docker network
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       MLflow           Airflow          FastAPI
      :5000             :8080            :8000
          │                │                │
          │                └──────┐         │
          │                       │         │
          └───────────────────────┴─────────┘
                      tracking URI

Host ./data
    │
    ├────────────── Airflow
    ├────────────── FastAPI
    └────────────── workspace
```

## Start stack

Dari root repository:

```bash
docker compose up -d --build
```

Cek status:

```bash
docker compose ps
```

Service utama:

```text
MLflow  -> http://localhost:5000
Airflow -> http://localhost:8080
FastAPI -> http://localhost:8000
```

## Service networking

Di dalam Docker network, service nggak pakai `localhost` buat saling komunikasi.

Contohnya FastAPI punya:

```text
MLFLOW_TRACKING_URI=http://mlflow:5000
```

Kenapa bukan:

```text
http://localhost:5000
```

karena `localhost` di container API berarti container API itu sendiri.

Docker Compose kasih DNS berdasarkan service name:

```text
mlflow
api
airflow
```

Makanya API dan Airflow bisa reach MLflow lewat hostname `mlflow`.

## Persistent volumes

Kita pakai tiga named volumes.

### mlflow-data

Nyimpen:

```text
SQLite metadata
MLflow artifacts
Model Registry state
```

Jadi stop container nggak langsung ngilangin experiment.

### airflow-home

Nyimpen:

```text
Airflow database
logs
generated local auth password
config
```

### dvc-cache

Dipakai Airflow dan workspace untuk cache DVC lokal.

## Shared data

Folder host:

```text
./data
```

di-bind ke:

```text
/app/data
```

di Airflow, API, dan workspace.

Jadi:

```text
Airflow bikin processed demand
        ↓
file muncul di host ./data
        ↓
FastAPI bisa baca history yang sama
```

## Bootstrap lewat workspace container

Service `workspace` sengaja pakai profile supaya dia nggak hidup terus.

Jalankan command one-shot:

```bash
docker compose run --rm workspace python scripts/bootstrap_data.py

docker compose run --rm workspace \
  python scripts/prepare_historical_demand.py

docker compose run --rm workspace \
  python scripts/build_features.py
```

Kalau mau bikin DVC snapshot:

```bash
docker compose run --rm workspace \
  dvc repro create_training_snapshot
```

## MLflow

MLflow server di container pakai:

```text
SQLite backend
+
proxied artifact storage
```

Untuk local workshop ini cukup.

Kita belum pakai PostgreSQL karena tujuan sekarang adalah ngerti relationship antar service, bukan bikin production-grade control plane.

Kalau nanti stack mau dibuat lebih production-like, backend MLflow dan metadata Airflow bisa dipindah ke database terpisah.

## Airflow login

Airflow 3 standalone generate password local.

Lihat file-nya:

```bash
docker compose exec airflow \
  cat /airflow/simple_auth_manager_passwords.json.generated
```

Atau lihat logs:

```bash
docker compose logs airflow
```

Airflow standalone memang cocok buat local development, bukan deployment production. citeturn414372search3

## Logs

Semua service:

```bash
docker compose logs -f
```

Satu service:

```bash
docker compose logs -f api
docker compose logs -f mlflow
docker compose logs -f airflow
```

## Stop

Stop container tanpa hapus state:

```bash
docker compose down
```

Kalau benar-benar mau reset named volumes juga:

```bash
docker compose down -v
```

Hati-hati, command kedua menghapus metadata MLflow dan state Airflow lokal.

## Typical workshop flow

```bash
docker compose up -d --build

docker compose run --rm workspace python scripts/bootstrap_data.py
docker compose run --rm workspace python scripts/prepare_historical_demand.py
docker compose run --rm workspace python scripts/build_features.py

docker compose ps
```

Setelah itu:

```text
Airflow UI
→ trigger pipeline

MLflow UI
→ inspect experiment / registry

FastAPI /docs
→ coba prediction
```

FastAPI baru bisa predict setelah registry punya alias `champion`.
