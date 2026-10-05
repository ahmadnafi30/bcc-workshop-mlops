# Grafana — Turning Metrics Into a Control Room

## Prometheus punya data, tapi manusia butuh view yang cepat dibaca

Prometheus UI bagus buat query.

Tapi kalau tiap pagi operator harus ketik 10 PromQL query manual, kurang convenient.

Grafana memberi dashboard.

Analogi:

~~~text
Prometheus
→ sensor database

Grafana
→ control room screen
~~~

---

# Datasource

Grafana connect ke Prometheus:

~~~text
http://prometheus:9090
~~~

Dalam Compose network.

Datasource config kita provision automatically.

Jadi participant nggak harus klik setup datasource manual.

---

# Dashboard provisioning

Config:

~~~text
monitoring/grafana/
├── provisioning/
└── dashboards/
~~~

Dashboard JSON disimpan di Git.

Kenapa?

Supaya dashboard reproducible.

~~~text
git clone
docker compose up
↓
same dashboard appears
~~~

Bukan:

> “Dashboard cuma ada di laptop presenter.”

---

# Dashboard kita

Panel awal:

~~~text
API Request Rate
API p95 Latency
Predictions in 5m
Retrain Recommended
Recent MAE vs Reference MAE
API Latency p50/p95
Current Model Version
~~~

Setiap panel harus answer question.

Bukan sekadar biar dashboard ramai.

---

# Generate API traffic

Kalau dashboard kosong, ya karena belum ada traffic.

Run:

~~~bash
uv run python scripts/generate_api_traffic.py   --date 2025-01-28   --start-hour 17   --end-hour 18
~~~

Script ini benar-benar HTTP call ke FastAPI.

Jadi:

- request counter naik,
- latency histogram terisi,
- prediction log juga terisi.

---

# replay_predictions.py berbeda

Ada script:

~~~text
replay_predictions.py
~~~

Ini call predictor directly.

Useful untuk batch evaluation cepat.

Tapi dia bypass HTTP layer.

Jadi API request metrics tidak naik.

Ini intentional distinction.

---

# p50 vs p95

## p50

Median.

Half requests faster, half slower.

## p95

95% request at or below threshold.

Kalau:

~~~text
p50 = 50 ms
p95 = 900 ms
~~~

most request cepat tapi tail cukup buruk.

Average mungkin hide pattern ini.

---

# Recent MAE vs reference MAE

Dashboard model panel compare:

~~~text
recent production-like MAE
vs
champion validation MAE
~~~

Ini memberi visual apakah current quality drifting away from baseline quality.

---

# Retrain Recommended

Gauge:

~~~text
0
→ no

1
→ yes
~~~

Ini bukan command buat retrain.

Ini decision signal.

Airflow monitoring DAG kemudian use logic yang sama.

---

# Current Model Version

Panel menunjukkan Registry model metadata.

Kenapa useful?

Kalau MAE tiba-tiba berubah setelah promotion, operator bisa correlate:

~~~text
model version changed
↓
metric behavior changed
~~~

---

# Dashboard empty troubleshooting chain

Debug dari source.

~~~text
1. API alive?
2. traffic generated?
3. /metrics has values?
4. Prometheus target UP?
5. Prometheus query returns?
6. Grafana datasource works?
7. panel query correct?
~~~

Jangan langsung edit dashboard kalau upstream metric belum ada.

---

# Dashboard is not monitoring logic

Grafana hanya visualization.

Retraining logic tidak hidup di Grafana.

Flow:

~~~text
prediction log
↓
evaluation script
↓
performance summary
↓
FastAPI metric
↓
Prometheus
↓
Grafana
~~~

Grafana adalah last-mile visualization.

---

# Future additions

Bisa tambah:

- alerting,
- CPU/memory exporter,
- data freshness,
- drift dashboard,
- error rate,
- SLA/SLO.

Tapi core dashboard kita sengaja kecil dan explainable.

Quality over number of panels.
