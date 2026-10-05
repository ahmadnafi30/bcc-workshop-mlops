# Prometheus

## What Prometheus does

Prometheus collects numeric time-series metrics.

It works mainly through a pull model:

~~~text
Prometheus
   ↓ scrape
FastAPI /metrics
~~~

Every few seconds Prometheus asks the API:

> What are your metric values now?

## Metrics endpoint

FastAPI exposes:

~~~text
/metrics
~~~

The response follows the Prometheus exposition format.

You normally do not read the entire output manually. Prometheus scrapes and stores it.

## Metric types in our project

### Counter

A value that increases.

Example:

~~~text
taxi_api_requests_total
~~~

Useful question:

> How many requests happened?

### Histogram

Collects a distribution into buckets.

Example:

~~~text
taxi_api_request_duration_seconds
~~~

This supports latency percentile estimates such as p95.

### Gauge

A value that can move up or down.

Example:

~~~text
taxi_model_recent_mae
~~~

## Metrics we expose

Operational:

~~~text
taxi_api_requests_total
taxi_api_request_duration_seconds
taxi_predictions_total
taxi_prediction_trip_count
taxi_model_version_info
~~~

Model monitoring:

~~~text
taxi_model_recent_mae
taxi_model_reference_mae
taxi_model_retrain_recommended
taxi_model_evaluated_predictions
~~~

## Labels

Prometheus metrics can have labels.

Example:

~~~text
method=POST
path=/predict
status=200
~~~

Labels are powerful but dangerous when they have too many unique values.

## Cardinality

Imagine using request_id as a label.

Every request creates a new time series.

That can explode storage and memory usage.

So we avoid arbitrary high-cardinality labels such as:

- request ID,
- user ID,
- every timestamp,
- every raw URL.

Detailed prediction data belongs in logs or tables, not Prometheus labels.

## Scrape config

Our config points to:

~~~text
api:8000/metrics
~~~

Inside Docker Compose, api is the service hostname.

## Open Prometheus

~~~text
http://localhost:9090
~~~

Try a query:

~~~text
taxi_api_requests_total
~~~

Then try a rate:

~~~text
sum(rate(taxi_api_requests_total[1m]))
~~~

The second query changes the question from total count to request rate.

## Prometheus is not a dashboard tool

Prometheus has a simple query UI, but Grafana becomes the main visualization layer.

Think:

~~~text
Prometheus
→ collect + query

Grafana
→ visualize
~~~
