# Architecture — Gimana Semua Komponen Ini Nyambung?

Kalau lihat architecture full dari awal, reaction pertama mungkin:

> “Wah banyak banget.”

Fair.

Jadi kita pecah jadi tiga perspective:

~~~text
1. Data Flow
2. Model Lifecycle
3. Operations Flow
~~~

Kalau tiga ini sudah kebayang, architecture keseluruhan jadi jauh lebih masuk akal.

---

## 1. Data Flow

Data flow jawab:

> “Data dari mana dan berubah jadi apa sebelum model belajar?”

~~~text
NYC TLC Trip Records
        ↓
Filter Manhattan
        ↓
Historical Replay Source
        ↓
Daily Raw Batch
        ↓
Hourly Zone Demand
        ↓
Feature Engineering
        ↓
Training Snapshot
~~~

Raw data itu one row per trip.

Model tidak train langsung dari trip rows. Kita aggregate menjadi:

~~~text
one row
=
one zone × one hour
~~~

Lalu dari history demand kita buat lag dan rolling features.

Folder data juga mengikuti lifecycle:

~~~text
source
→ external/original input

raw
→ released daily batch

processed
→ hourly demand

features
→ model-ready table

snapshots
→ frozen training input
~~~

Jadi nama folder bukan sekadar estetika. Dia merepresentasikan data lifecycle.

---

## 2. Model Lifecycle

Model lifecycle jawab:

> “Dari training data sampai model yang live, prosesnya bagaimana?”

~~~text
Training Snapshot
       ↓
Train Baseline
       ↓
Train Main Model
       ↓
Evaluate
       ↓
MLflow Tracking
       ↓
Model Registry
       ↓
Challenger
       ↓
Review
       ↓
Champion
       ↓
Serving
~~~

Kenapa ada baseline? Karena complex model harus earn complexity-nya.

Kenapa ada Registry? Karena experiment bagus belum otomatis production model.

Kenapa ada challenger dan champion? Supaya promotion explicit dan traceable.

---

## 3. Operations Flow

Operations flow jawab:

> “Setelah model diserve, kita tahu system-nya sehat dari mana?”

~~~text
Client Request
      ↓
FastAPI
      ↓
Prediction
      ↓
Operational Metrics
      ↓
Prometheus
      ↓
Grafana
~~~

Tapi itu baru system health.

Untuk model health:

~~~text
Prediction
      ↓
Prediction Log
      ↓
Ground Truth Arrives
      ↓
Join Prediction + Actual
      ↓
MAE / RMSE
      ↓
Retrain Decision
~~~

Dua loop ini jalan paralel.

---

## Mapping ke repository

### src/

Reusable business logic.

Contoh:

~~~text
src/ingestion/
src/features/
src/training/
src/serving/
src/monitoring/
~~~

Rule penting:

> Logic yang bisa dipakai ulang jangan ditaruh hanya di script atau DAG.

### scripts/

Human-friendly entry points.

Script mostly call reusable function dari src.

### dags/

Airflow orchestration.

Rule:

~~~text
dags
→ WHEN + IN WHAT ORDER

src
→ HOW
~~~

Kalau business logic numpuk di DAG, testing jadi susah.

### api/

HTTP layer.

Responsibility-nya request, response, status code, dependency wiring. Feature construction dan model loading tetap reusable di serving layer.

### monitoring/

Prometheus dan Grafana configuration.

Ini infrastructure concern, bukan training logic.

---

## Kenapa boundaries penting?

Bayangin semua logic ditaruh di satu main.py 3000 lines.

Ada data download, feature engineering, training, serving, monitoring, orchestration.

Technically mungkin jalan, tapi maintainability jelek.

Boundary membantu jawab:

> “Kalau feature engineering berubah, concern mana yang kita sentuh?”

> “Kalau API response berubah, apa yang seharusnya nggak ikut berubah?”

> “Kalau orchestration berubah tapi domain logic sama, file mana yang relevan?”

Architecture bagus bukan karena folder-nya banyak. Architecture bagus karena responsibility jelas.

---

## Local vs Container Network

Ini sering bikin newbie bingung.

Dari browser host:

~~~text
MLflow
http://localhost:5000
~~~

Dari API container:

~~~text
http://mlflow:5000
~~~

Kenapa beda?

Karena localhost artinya “machine/container saya sendiri”.

Di API container, localhost:5000 berarti port 5000 di API container, bukan MLflow container.

Docker Compose kasih internal DNS berdasarkan service name.

Jadi:

~~~text
api
→ mlflow:5000

prometheus
→ api:8000

grafana
→ prometheus:9090
~~~

Ini concept networking yang bakal sering muncul.

---

## Simplification vs real production

Production platform bisa jauh lebih kompleks.

Tapi yang berubah biasanya scale dan infrastructure.

~~~text
local filesystem
→ object storage

single Docker host
→ Kubernetes

SQLite
→ managed database

standalone Airflow
→ distributed/managed Airflow
~~~

Pattern lifecycle tetap sama.

Makanya kita belajar pattern dulu.
