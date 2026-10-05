# Step 9 — Monitoring: Bikin Dashboard Benar-Benar Bergerak

Sekarang stack hidup.

Prometheus dan Grafana ada.

Tapi dashboard tanpa traffic ya kosong.

Kita generate real API traffic dan kemudian evaluate model quality.

---

## Goal

Setelah step ini:

- API operational metrics bergerak,
- Prometheus query works,
- Grafana dashboard punya data,
- prediction log dievaluate,
- recent MAE muncul,
- kalian ngerti system vs model monitoring.

---

## 1. Open Grafana sebelum traffic

~~~text
http://localhost:3000
~~~

Dashboard mungkin mostly zero/empty.

Ini bagus buat comparison before-after.

---

## 2. Generate HTTP traffic

~~~bash
uv run python scripts/generate_api_traffic.py   --date 2025-01-28   --start-hour 17   --end-hour 18
~~~

Script ini call FastAPI.

Kenapa bukan direct predictor?

Karena kita pengen exercise:

~~~text
HTTP middleware
request count
latency
prediction log
~~~

---

## 3. Refresh Grafana

Wait beberapa detik buat Prometheus scrape.

Lihat:

- request rate,
- p95 latency,
- prediction count,
- model version.

Question:

> “Kalau request rate belum naik, chain mana yang mungkin belum jalan?”

Traffic → API → metrics → Prometheus → Grafana.

Debug from left to right.

---

## 4. Open Prometheus

~~~text
http://localhost:9090
~~~

Query:

~~~text
taxi_api_requests_total
~~~

Lihat raw series.

Then:

~~~text
sum(rate(taxi_api_requests_total[1m]))
~~~

Apa bedanya?

Counter vs rate.

---

## 5. Check prediction log

~~~text
data/monitoring/predictions.jsonl
~~~

Sekarang banyak entries.

Tapi belum otomatis punya actual error.

Need ground truth match.

---

## 6. Evaluate predictions

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

Observe terminal.

Expected summary fields:

~~~text
reference MAE
recent MAE
threshold
evaluation count
retrain recommended
~~~

---

## 7. Open performance summary

~~~text
data/monitoring/performance_summary.json
~~~

Read values.

Tanya:

> “Kalau retrain_recommended false, apakah monitoring gagal?”

No.

Itu valid decision.

---

## 8. Refresh Grafana

Wait scrape.

Recent MAE dan reference MAE harus mulai muncul kalau evaluation available.

---

## 9. Operational vs model scenario

Coba discuss:

### Scenario 1

~~~text
p95 latency low
HTTP success
recent MAE high
~~~

Action focus model.

### Scenario 2

~~~text
recent MAE normal
p95 latency huge
~~~

Action focus service/infrastructure.

Monitoring membantu classify problem.

---

## 10. Direct replay distinction

Ada:

~~~text
replay_predictions.py
~~~

Ini direct predictor, useful buat fast batch model evaluation.

Tapi bypass HTTP.

Jadi jangan expect API latency panel bergerak kalau pakai script itu.

Use correct tool for intended signal.

---

## Mini challenge

Kenapa prediction detail nggak dimasukkan semua sebagai Prometheus labels?

Cardinality.

Detailed event → log/table.

Aggregate metric → Prometheus.

---

## Checkpoint

1. Scrape itu apa?
2. Counter vs rate?
3. p95 latency?
4. Prediction log kenapa perlu?
5. Ground truth datang kapan?
6. Model healthy vs service healthy beda apa?
7. retrain_recommended false bisa jadi success nggak?
