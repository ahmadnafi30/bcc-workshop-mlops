# Step 9 — Monitoring: Is the API Healthy, and Is the Model Still Good?

Ini section yang biasanya bikin MLOps mulai “klik”.

Karena sekarang kita lihat:

> model selesai deploy bukan end of story.

Kita perlu observe.

---

# Keep Compose running

Pastikan:

~~~bash
docker compose ps
~~~

service API, Prometheus, Grafana healthy/running.

---

# Part A — Operational metrics

## 1. Open raw metrics

~~~text
http://localhost:8000/metrics
~~~

Kalian akan lihat banyak text.

Nggak harus dibaca semua.

Cari:

~~~text
taxi_api_requests_total
~~~

Kalau belum ada traffic, value mungkin kecil/zero.

---

# 2. Generate HTTP traffic

Run from host environment:

~~~bash
uv run python scripts/generate_api_traffic.py   --date 2025-01-28   --start-hour 17   --end-hour 18
~~~

Script hit FastAPI untuk multiple Manhattan zones.

---

# 3. Observe terminal output

Success vs failed count.

Kalau banyak failed 422, likely history issue.

Jangan lanjut ke Grafana dulu sebelum traffic success.

---

# 4. Open Prometheus

~~~text
http://localhost:9090
~~~

Query:

~~~text
taxi_api_requests_total
~~~

Lalu:

~~~text
sum(rate(taxi_api_requests_total[1m]))
~~~

Coba lihat beda bentuk result.

---

# 5. Open target page

Prometheus target API harus UP.

Kalau DOWN, debugging networking dulu.

---

# 6. Open Grafana

~~~text
http://localhost:3000
~~~

Dashboard:

~~~text
MLOps / Taxi Demand MLOps
~~~

Lihat:

- request rate,
- p95 latency,
- predictions,
- model version.

---

# Part B — Model performance

Operational dashboard belum jawab:

> Prediction-nya bener nggak?

Sekarang ground truth evaluation.

---

# 7. Inspect prediction log

~~~text
data/monitoring/predictions.jsonl
~~~

Kalian harus lihat prediction records dari API calls.

---

# 8. Run evaluation

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

Script:

~~~text
load predictions
↓
find actual demand
↓
join
↓
calculate error
↓
summary
~~~

---

# 9. Inspect evaluation table

~~~text
data/monitoring/evaluations.parquet
~~~

Optional:

~~~bash
uv run python -c "import pandas as pd; print(pd.read_parquet('data/monitoring/evaluations.parquet').head())"
~~~

Lihat:

~~~text
predicted_trip_count
actual_trip_count
absolute_error
squared_error
~~~

---

# 10. Inspect performance summary

~~~text
data/monitoring/performance_summary.json
~~~

Cari:

~~~text
recent_mae
reference_mae
threshold_mae
evaluation_count
retrain_recommended
~~~

---

# 11. Wait Prometheus scrape

FastAPI /metrics refresh model performance gauges from summary.

Prometheus scrape period beberapa detik.

Setelah itu Grafana panel MAE muncul/update.

---

# 12. Interpret, don't just watch charts

Pertanyaan yang harus kalian jawab:

### System health

- request jalan?
- latency okay?
- errors?

### Model health

- recent MAE berapa?
- reference MAE berapa?
- sample cukup?
- retrain recommended?

---

# API traffic vs direct replay

Workshop punya dua scripts.

## generate_api_traffic.py

~~~text
HTTP
↓
FastAPI
↓
operational metrics
↓
prediction log
~~~

## replay_predictions.py

~~~text
direct predictor
↓
prediction log
~~~

Lebih cepat buat model evaluation batch, tapi bypass HTTP metrics.

Gunakan sesuai purpose.

---

# Mini challenge

Case:

~~~text
p95 latency = 50 ms
HTTP errors = 0
recent MAE = 30
reference MAE = 10
~~~

Apakah system healthy?

Jawaban:

Operationally iya.

Model-wise tidak.

Itulah kenapa dua monitoring dimension diperlukan.

---

# Checkpoint

Kalian siap retraining section kalau bisa explain:

> Kenapa model MAE nggak bisa dihitung saat prediction request baru masuk?

Karena ground truth target belum tersedia.
