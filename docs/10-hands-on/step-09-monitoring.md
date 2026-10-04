# Step 9 — Prometheus and Grafana Monitoring

## Goal

Generate real API traffic, collect operational metrics, then calculate model performance using ground truth.

Keep Docker Compose running.

## 1. Metrics endpoint

Open:

~~~text
http://localhost:8000/metrics
~~~

The raw text is meant for Prometheus scraping.

## 2. Generate real HTTP traffic

~~~bash
uv run python scripts/generate_api_traffic.py \
  --date 2025-01-28 \
  --start-hour 17 \
  --end-hour 18
~~~

This calls POST /predict through FastAPI.

Therefore it creates:

~~~text
API counters + latency
and
prediction logs
~~~

## 3. Two replay scripts, two purposes

~~~text
generate_api_traffic.py
→ through HTTP
→ operational metrics + prediction log

replay_predictions.py
→ predictor directly
→ faster batch model evaluation
~~~

## 4. Prometheus

Open:

~~~text
http://localhost:9090
~~~

Try:

~~~text
taxi_api_requests_total
~~~

Then:

~~~text
sum(rate(taxi_api_requests_total[1m]))
~~~

Counter and rate answer different questions.

## 5. Grafana

Open:

~~~text
http://localhost:3000
~~~

Dashboard:

~~~text
MLOps / Taxi Demand MLOps
~~~

Look for request rate, latency, prediction count, and current model version.

## 6. Evaluate against actual demand

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

Flow:

~~~text
prediction log
      +
processed ground truth
      ↓
MAE + RMSE
      ↓
performance summary
~~~

Generated:

~~~text
data/monitoring/evaluations.parquet
data/monitoring/performance_summary.json
~~~

## 7. Wait for scrape

FastAPI exposes values from the latest summary. Prometheus needs a scrape cycle before Grafana receives the new series value.

## 8. Interpret

Ask:

- Is the API healthy?
- Which model version is serving?
- Is recent MAE worse than reference?
- How many predictions were evaluated?
- Is retraining recommended?

## Checkpoint

You should understand why system health and model health need different evidence.
