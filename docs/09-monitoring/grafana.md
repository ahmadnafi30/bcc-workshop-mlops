# Grafana

Grafana dipakai buat visualisasi metric dari Prometheus.

Local UI:

```text
http://localhost:3000
```

Datasource dan dashboard sudah diprovision otomatis.

Jadi setelah stack hidup, dashboard:

```text
MLOps / Taxi Demand MLOps
```

langsung tersedia.

## Dashboard awal

Panel yang kita punya:

```text
API request rate
API p95 latency
predictions in 5 minutes
retrain recommended
recent MAE vs reference MAE
p50 / p95 latency
current model version
```

Dashboard file-nya:

```text
monitoring/grafana/dashboards/taxi-mlops.json
```

Provisioning datasource:

```text
monitoring/grafana/provisioning/datasources/prometheus.yml
```

## Generate traffic

Kalau dashboard sepi, kirim prediction request atau replay historical prediction:

```bash
uv run python scripts/replay_predictions.py --date 2025-01-28
```

Lalu evaluate ground truth:

```bash
uv run python scripts/evaluate_predictions.py
```

Saat Prometheus scrape berikutnya, `/metrics` baca summary performance terbaru dan Grafana mulai nampilin recent MAE.

## Kenapa dashboard diprovision dari file?

Biar dashboard jadi bagian dari repository.

Jadi bukan:

```text
"dashboard ada di laptop presenter"
```

tapi:

```text
git clone
docker compose up
dashboard yang sama muncul
```

Ini juga bikin perubahan dashboard bisa direview lewat Git.
