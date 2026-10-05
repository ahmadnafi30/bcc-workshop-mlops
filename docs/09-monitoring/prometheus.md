# Prometheus — Ngumpulin Angka System Health dari Service Kita

FastAPI sudah expose metrics.

Sekarang siapa yang collect angka itu over time?

Prometheus.

Prometheus adalah time-series monitoring system.

---

## Pull model

Prometheus biasanya scrape target.

~~~text
Prometheus
↓ GET
FastAPI /metrics
~~~

Setiap interval, dia ambil current metric sample.

Kenapa pull?

Prometheus central server tahu target dan schedule scraping.

Service cukup expose endpoint.

---

## Metric type: Counter

Counter only goes up, kecuali process restart reset.

Example:

~~~text
taxi_api_requests_total
~~~

Questions:

> Total request berapa?

Kalau mau request per second, kita derive rate dari counter.

---

## Metric type: Gauge

Gauge bisa naik/turun.

Example:

~~~text
taxi_model_recent_mae
~~~

MAE bisa berubah dua arah.

Gauge cocok.

---

## Metric type: Histogram

Histogram record observation distribution ke buckets.

Example:

~~~text
request latency
~~~

Kenapa nggak cuma average?

Average bisa hide tail latency.

Example:

~~~text
99 requests = 50 ms
1 request = 10 sec
~~~

Average mungkin still kelihatan okay-ish, tapi user unlucky dapat terrible latency.

Histogram support percentile estimation.

---

## p50, p95

### p50

Median-ish typical latency.

### p95

95% request ada di bawah/sekitar threshold itu.

Tail performance lebih terlihat.

---

## Labels

Metric bisa punya labels:

~~~text
method=POST
path=/predict
status=200
~~~

Label bikin one metric name punya dimension.

Powerful.

Tapi ada danger.

---

## Cardinality

Kalau label punya millions unique values:

~~~text
request_id
user_id
timestamp
arbitrary URL
~~~

Prometheus create tons of time series.

Memory/storage explode.

Makanya project normalize paths.

Detailed per-prediction info masuk logs/table, bukan Prometheus label.

---

## Scrape config

Prometheus config target:

~~~text
api:8000
~~~

Kenapa api bukan localhost?

Karena Prometheus container berada di Compose network.

Service DNS name = api.

---

## Query

Raw counter:

~~~text
taxi_api_requests_total
~~~

Rate:

~~~text
sum(rate(taxi_api_requests_total{path="/predict"}[1m]))
~~~

Yang satu jawab cumulative.

Yang satu jawab recent request rate.

Filter `path="/predict"` membuat panel fokus pada prediction traffic. Counter
mentah tetap memuat `/health`, `/metrics`, dan endpoint lainnya.

Error rate 5xx adalah proporsi kegagalan server dari seluruh request prediction:

~~~text
(sum(rate(taxi_api_requests_total{path="/predict",status=~"5.."}[5m])) or vector(0))
/
sum(rate(taxi_api_requests_total{path="/predict"}[5m]))
~~~

`or vector(0)` menyediakan numerator nol ketika ada traffic tetapi belum pernah
ada response 5xx. Dashboard juga mengecek denominator positif, sehingga error
rate belum tersedia saat tidak ada traffic. Query 4xx memakai pola `4..`.

Histogram latency di dashboard memakai filter path yang sama sebelum bucket
digabung. Health check yang cepat tidak ikut menurunkan p95 prediction.

PromQL memungkinkan transform time-series.

---

## Metric model tambahan

| Metric | Yang dibaca |
| --- | --- |
| `taxi_model_evaluation_status` | 0 belum dievaluasi, 1 sample kurang, 2 dalam batas, 3 perlu retrain. |
| `taxi_model_evaluated_predictions` | Jumlah prediction unik dengan actual dalam recent window. |
| `taxi_model_min_evaluation_samples` | Minimum sample untuk keputusan retraining. |
| `taxi_model_threshold_mae` | Reference MAE × multiplier dari job evaluasi. |
| `taxi_model_last_evaluation_timestamp_seconds` | Waktu nyata job evaluasi terakhir. |
| `taxi_model_latest_target_timestamp_seconds` | Target historical terakhir yang sudah dievaluasi. |
| `taxi_model_evaluated_version_info` | Identitas model sumber summary evaluasi. |

Metric MAE yang belum diketahui diekspos sebagai `NaN`. Saat summary kosong,
hilang, atau invalid, exporter menghapus nilai lama dan operational metrics tetap
bisa discrape. Summary ditulis lewat file sementara lalu diganti secara atomik
agar scrape tidak membaca JSON setengah jadi.

---

## Prometheus bukan log storage

Jangan masukkan entire prediction payload sebagai metric.

Metrics cocok buat numeric aggregate over time.

Logs/events cocok buat detailed record.

Different observability signals punya role berbeda.

---

## Checkpoint

1. Scrape itu apa?
2. Counter, Gauge, Histogram beda apa?
3. Kenapa p95 useful?
4. Apa itu cardinality?
5. Kenapa request_id buruk jadi label?
6. Metrics beda apa dengan prediction log?
