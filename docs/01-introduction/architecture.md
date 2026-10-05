# Architecture — How Everything Connects

## Jangan takut dulu sama diagramnya

Kalau kalian lihat architecture MLOps dari awal dalam satu gambar, reaksinya kadang:

> “Lah kok banyak banget service?”

Santai.

Architecture kita sebenarnya cuma gabungan dari beberapa simple flow yang saling connect.

Daripada lihat sebagai satu monster besar, kita pecah jadi:

~~~text
Data Flow
Model Lifecycle
Serving Flow
Monitoring Flow
Software Delivery Flow
~~~

Baru setelah ngerti masing-masing, kita gabungkan.

---

# 1. Data Flow

Semua dimulai dari official NYC TLC data.

~~~text
NYC TLC monthly parquet
        ↓
bootstrap
        ↓
compact replay source
        ↓
daily raw batch
        ↓
hourly demand
        ↓
feature engineering
        ↓
training-ready dataset
~~~

Raw TLC punya:

~~~text
1 row = 1 trip
~~~

Setelah aggregation:

~~~text
1 row = 1 zone × 1 hour
~~~

Setelah feature engineering:

~~~text
zone_id
hour
day_of_week
lag_1h
lag_24h
lag_168h
rolling_mean_3h
...
target_trip_count
~~~

Ini jalur data kita.

---

# 2. Training Flow

Training flow dimulai dari model-ready features.

~~~text
features
   ↓
training snapshot
   ↓
DVC
   ↓
time-based split
   ↓
naive baseline
   +
HistGradientBoosting
   ↓
MAE / RMSE
   ↓
MLflow Tracking
~~~

Kenapa ada snapshot?

Supaya training nggak bergantung ke file features yang terus berubah.

Kita freeze dataset sampai cutoff tertentu.

Misalnya:

~~~text
taxi_demand_2025-01-26.parquet
~~~

Sekarang experiment punya stable input.

---

# 3. Model Lifecycle

Setelah training, belum otomatis production.

~~~text
MLflow run
   ↓
register model version
   ↓
challenger
   ↓
review
   ↓
champion
~~~

Model Registry memisahkan dua konsep:

> Model yang berhasil ditrain.

dan:

> Model yang sudah approved untuk serving.

Itu beda.

---

# 4. Serving Flow

Client nggak perlu tahu feature engineering internal.

Dia cuma kirim:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Lalu:

~~~text
FastAPI
   ↓
validate request
   ↓
load history
   ↓
build online features
   ↓
load MLflow champion
   ↓
predict
   ↓
log prediction
   ↓
response
~~~

Important point:

> Client nggak kirim lag_168h.

Kenapa?

Karena lag feature adalah implementation detail model.

Kalau external client harus tahu semua feature internals, serving contract jadi terlalu coupled ke model.

---

# 5. Monitoring Flow

Prediction langsung kita log.

Tapi saat prediction dibuat, actual target belum tersedia.

Misalnya:

~~~text
17:00
predict demand for 18:00

18:00–18:59
actual taxi trips happen

afterward
actual 18:00 demand becomes available
~~~

Jadi evaluation terjadi delayed.

~~~text
prediction log
     +
actual demand later
     ↓
absolute error
     ↓
recent MAE
     ↓
performance summary
~~~

Di sisi operational:

~~~text
FastAPI /metrics
      ↓
Prometheus
      ↓
Grafana
~~~

Jadi ada dua jalur monitoring.

---

# 6. Retraining Flow

Kalau recent MAE melewati threshold:

~~~text
recent MAE
>
champion validation MAE × multiplier
~~~

dan jumlah sample cukup:

~~~text
monitoring
   ↓
create newer snapshot
   ↓
retrain
   ↓
validate
   ↓
log to MLflow
   ↓
register challenger
~~~

Tapi:

~~~text
challenger
≠
automatically champion
~~~

Promotion masih explicit.

---

# 7. Orchestration Flow

Airflow mengatur kapan dan urutan beberapa flow.

Kita punya tiga DAG utama.

## Daily replay

~~~text
get_replay_date
      ↓
release_batch
      ↓
validate_batch
      ↓
aggregate_demand
      ↓
rebuild_features
~~~

## Initial training

~~~text
create_snapshot
      ↓
train_model
      ↓
register_candidate
~~~

## Monitoring

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Airflow tidak replace Python logic.

Dia orchestrate Python logic.

---

# 8. Container Architecture

Docker Compose nyalain service:

~~~text
MLflow
Airflow
FastAPI
Prometheus
Grafana
~~~

Mereka hidup sebagai container terpisah.

Kenapa terpisah?

Karena responsibility-nya beda.

~~~text
FastAPI
→ serve prediction

MLflow
→ experiment + registry

Airflow
→ orchestration

Prometheus
→ collect metrics

Grafana
→ visualize metrics
~~~

Ini namanya separation of concerns.

---

# 9. Networking antar service

Dari browser laptop kalian:

~~~text
MLflow
http://localhost:5000

FastAPI
http://localhost:8000
~~~

Tapi dari dalam container API:

~~~text
http://mlflow:5000
~~~

Bukan localhost.

Kenapa?

Karena:

> localhost di dalam container berarti container itu sendiri.

Docker Compose menyediakan internal DNS berdasarkan service name.

Jadi:

~~~text
api → mlflow:5000
prometheus → api:8000
grafana → prometheus:9090
~~~

---

# 10. Software Delivery Flow

MLOps project tetap software project.

Ada source code lifecycle juga.

~~~text
feat/*
   ↓
Pull Request
   ↓
develop
   ↓
CI
   ↓
develop → main
   ↓
CI
   ↓
Container Delivery
   ↓
GHCR
~~~

GitHub Actions mengurus repository-level automation.

Ini beda dengan Airflow.

---

# Airflow vs GitHub Actions

Biar nggak ketuker:

## Airflow

Trigger karena data / ML workflow.

Contoh:

~~~text
new daily taxi batch
↓
run processing pipeline
~~~

## GitHub Actions

Trigger karena repository event.

Contoh:

~~~text
pull request opened
↓
run tests
~~~

Jadi:

~~~text
Airflow
→ data lifecycle

GitHub Actions
→ code lifecycle
~~~

---

# Big picture akhirnya

Kalau digabung:

~~~text
                    ┌──────────────────┐
                    │   NYC TLC Data   │
                    └────────┬─────────┘
                             │
                             v
                    Data Preparation
                             │
                             v
                    Feature Engineering
                             │
                             v
                       DVC Snapshot
                             │
                             v
                         Training
                             │
                             v
                    MLflow Tracking
                             │
                             v
                     Model Registry
                             │
                       champion alias
                             │
                             v
                         FastAPI
                             │
                  ┌──────────┴──────────┐
                  │                     │
                  v                     v
          prediction response     prediction log
                                        │
                                        v
                                  ground truth
                                        │
                                        v
                                   recent MAE
                                        │
                                        v
                                    Airflow
                                        │
                                  retrain?
                                        │
                                        v
                                    challenger
~~~

Di samping itu:

~~~text
FastAPI
  ↓ metrics
Prometheus
  ↓
Grafana
~~~

dan:

~~~text
Git Push
  ↓
GitHub Actions
  ↓
CI
  ↓
GHCR
~~~

Sekarang architecture-nya memang lebih banyak, tapi setiap bagian punya satu responsibility yang jelas.

Kalau nanti kalian bingung satu service buat apa, jangan lihat full diagram.

Tanya aja:

> “Service ini sedang menyelesaikan problem yang mana?”
