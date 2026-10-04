# Prometheus

FastAPI expose metric di:

```text
GET /metrics
```

Prometheus scrape endpoint itu setiap beberapa detik.

## Metric yang kita punya

Operational:

```text
taxi_api_requests_total
taxi_api_request_duration_seconds
taxi_predictions_total
taxi_prediction_trip_count
taxi_model_version_info
```

Model monitoring:

```text
taxi_model_recent_mae
taxi_model_reference_mae
taxi_model_retrain_recommended
taxi_model_evaluated_predictions
```

## Kenapa nggak pakai zone_id sebagai label?

Zone kita lumayan banyak.

Kalau setiap metric dikasih label arbitrary seperti:

```text
zone_id
user_id
request_id
```

jumlah time series bisa meledak.

Makanya metric operational cuma pakai label yang cardinality-nya kecil seperti:

```text
method
path
status
model_version
```

Detail per prediction tetap masuk prediction log, bukan dijadikan Prometheus label.

## Local stack

Prometheus sudah masuk Docker Compose:

```bash
docker compose up -d --build
```

UI:

```text
http://localhost:9090
```

Config:

```text
monitoring/prometheus/prometheus.yml
```

Target scrape:

```text
api:8000/metrics
```

Karena Prometheus ada di Docker network yang sama, dia pakai service name `api`, bukan localhost.
