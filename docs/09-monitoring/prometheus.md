# Prometheus — Collecting Operational Metrics

## Prometheus masuk karena kita butuh time-series metrics

FastAPI bisa print log.

Tapi kalau kita mau answer:

> Request rate lima menit terakhir berapa?

> p95 latency?

> Prediction count?

kita butuh metrics system.

Prometheus adalah tool yang kita pakai.

---

# Pull model

Prometheus default bekerja dengan scrape.

~~~text
Prometheus
    ↓ GET
FastAPI /metrics
~~~

Setiap interval, Prometheus tarik current metrics.

Bukan API yang push setiap metric event ke Prometheus.

---

# /metrics

FastAPI expose:

~~~text
GET /metrics
~~~

Output bukan JSON biasa.

Prometheus exposition format.

Kalian nggak perlu manually parse.

Prometheus collector yang consume.

---

# Metric types

## Counter

Monotonically increases.

Contoh:

~~~text
taxi_api_requests_total
~~~

Use:

> total event count.

Untuk rate:

~~~text
rate(counter[1m])
~~~

---

## Histogram

Collect observation ke buckets.

Contoh:

~~~text
taxi_api_request_duration_seconds
~~~

Useful buat latency distribution.

Kita bisa derive approximate percentile seperti p95.

---

## Gauge

Value bisa naik turun.

Contoh:

~~~text
taxi_model_recent_mae
~~~

MAE bisa improve/worsen.

Gauge cocok.

---

# Operational metrics

Project expose:

~~~text
taxi_api_requests_total
taxi_api_request_duration_seconds
taxi_predictions_total
taxi_prediction_trip_count
taxi_model_version_info
~~~

---

# Model performance gauges

Juga expose summary:

~~~text
taxi_model_recent_mae
taxi_model_reference_mae
taxi_model_retrain_recommended
taxi_model_evaluated_predictions
~~~

Values berasal dari performance summary artifact.

Jadi Prometheus tidak calculate MAE from raw prediction logs.

Evaluation pipeline yang calculate.

Prometheus hanya expose time-series signal.

---

# Labels

Counter bisa punya labels:

~~~text
method
path
status
~~~

Contoh conceptual:

~~~text
POST
/predict
200
~~~

Labels powerful karena query flexible.

Tapi danger: cardinality.

---

# Cardinality

Bayangin label:

~~~text
request_id
~~~

Setiap request unique.

Prometheus harus maintain new time series per request.

Bad.

Begitu juga arbitrary user IDs.

Makanya kita pilih low-cardinality labels.

---

# Kenapa zone_id tidak jadi label?

Manhattan zones memang nggak millions, tapi lesson-nya tetap:

> Detailed business dimensions tidak selalu cocok dijadikan metrics label.

Per-prediction detail ada di logs/evaluation table.

Prometheus focus aggregated operational metrics.

---

# Scrape configuration

File:

~~~text
monitoring/prometheus/prometheus.yml
~~~

Target:

~~~text
api:8000
~~~

Kenapa api, bukan localhost?

Karena Prometheus running inside Compose network.

---

# Open UI

~~~text
http://localhost:9090
~~~

Try query:

~~~text
taxi_api_requests_total
~~~

Then:

~~~text
sum(rate(taxi_api_requests_total[1m]))
~~~

Difference:

~~~text
counter total
vs
request rate
~~~

---

# p95 latency

Histogram query can approximate p95.

Meaning:

> roughly 95% requests complete at or below this latency threshold.

Kenapa p95 sometimes more useful daripada mean?

Karena average bisa hide slow tail.

---

# Target status

Prometheus UI punya target page.

Kalau API scrape fail:

~~~text
target DOWN
~~~

First debug networking / service health before blaming Grafana.

---

# Prometheus vs logs

Metrics:

~~~text
How much?
How often?
How fast?
~~~

Logs:

~~~text
What exactly happened?
~~~

Mereka complement.

Jangan pakai metrics sebagai replacement semua logs.

---

# Checkpoint

Prometheus di project kita:

> collect + store + query time-series signals.

Visualization utama nanti Grafana.
