# Grafana — Dari Metric Mentah Jadi Dashboard yang Bisa Dibaca Manusia

Prometheus punya data.

Tapi kalau setiap kali mau inspect system kita harus ngetik query satu-satu, kurang nyaman.

Grafana jadi visualization layer.

Mental model:

~~~text
Prometheus
→ collect + query

Grafana
→ visualize + dashboard
~~~

---

## Datasource

Grafana perlu tahu data source.

Project provision:

~~~text
Prometheus
http://prometheus:9090
~~~

Di Compose network, hostname prometheus resolve ke Prometheus container.

---

## Provisioning

Dashboard kita tidak dibuat manual lalu cuma hidup di laptop presenter.

Config disimpan di repo.

~~~text
monitoring/grafana/
├── provisioning/
└── dashboards/
~~~

Benefit:

~~~text
git clone
↓
docker compose up
↓
same dashboard
~~~

Dashboard jadi code/config artifact.

Bisa versioned dan reviewed.

---

## Panel utama

Dashboard menampilkan:

- API request rate,
- p95 latency,
- prediction count,
- recent MAE,
- reference MAE,
- retrain recommendation,
- current model version.

Kenapa combine operational + model metric?

Supaya satu view bisa bantu differentiate:

~~~text
service problem
vs
model problem
~~~

---

## Dashboard empty bukan berarti broken

Kalau belum ada traffic:

~~~text
request rate = no data / zero
~~~

Normal.

Generate actual API traffic:

~~~bash
uv run python scripts/generate_api_traffic.py   --date 2025-01-28   --start-hour 17   --end-hour 18
~~~

Kenapa script ini lewat HTTP?

Supaya middleware metrics beneran triggered.

Direct predictor replay nggak create HTTP latency metric.

---

## Data chain

Kalau recent MAE panel kosong, debug chain:

~~~text
prediction happened?
↓
prediction log written?
↓
ground truth exists?
↓
evaluate_predictions ran?
↓
performance_summary exists?
↓
/metrics exposes gauge?
↓
Prometheus scraped?
↓
Grafana query correct?
~~~

Observability debugging juga perlu dependency thinking.

---

## Dashboard bukan source of truth sendiri

Grafana visualize.

Dia bukan tempat business logic retrain.

Decision summary dihasilkan monitoring pipeline.

Prometheus scrape metric.

Grafana visualize.

Separation:

~~~text
logic
→ monitoring code

metrics storage
→ Prometheus

visualization
→ Grafana
~~~

---

## Alerting?

Grafana/Prometheus ecosystem bisa alert.

Workshop belum fokus ke alert channel.

Future extension:

~~~text
retrain_recommended = 1
↓
alert
↓
Slack/email/on-call
~~~

Tapi jangan buru-buru add alert sebelum metric quality jelas.

---

## Checkpoint

1. Grafana beda apa dengan Prometheus?
2. Provisioning dashboard benefit-nya apa?
3. Kenapa dashboard bisa kosong padahal Grafana sehat?
4. Kalau MAE panel kosong, dependency chain apa yang dicek?
5. Kenapa retraining logic nggak ditaruh di Grafana?
