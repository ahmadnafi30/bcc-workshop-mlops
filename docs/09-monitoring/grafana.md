# Grafana

## What Grafana adds

Prometheus stores and queries metrics.

Grafana turns them into dashboards that are easier for humans to scan.

Analogy:

~~~text
Prometheus
→ database + calculator

Grafana
→ control room screens
~~~

## Provisioning

Our dashboard and datasource are stored in Git.

~~~text
monitoring/grafana/
├── provisioning/
└── dashboards/
~~~

Why is this better than manually clicking a dashboard together?

Because:

~~~text
git clone
docker compose up
→ same dashboard
~~~

The dashboard becomes reproducible configuration.

## Datasource

Grafana connects to:

~~~text
http://prometheus:9090
~~~

Again, service-to-service communication uses Docker service names.

## Dashboard panels

The starter dashboard includes:

- API request rate,
- API p95 latency,
- prediction count,
- retraining recommendation,
- recent MAE,
- reference MAE,
- current model version.

## p50 vs p95

Suppose latency is usually fast, but a few requests are very slow.

Average latency can hide that.

Percentiles help answer:

~~~text
p50
→ typical middle request

p95
→ 95% of requests are at or below this latency
~~~

p95 is often useful for spotting poor tail behavior.

## Open Grafana

~~~text
http://localhost:3000
~~~

The dashboard is provisioned under the MLOps folder.

## Empty dashboard?

A dashboard cannot visualize traffic that never happened.

Generate requests or historical prediction replay.

Then give Prometheus a scrape interval to collect the metrics.

## Dashboard is not the monitor itself

Grafana does not magically know model quality.

The chain is:

~~~text
prediction logs
↓
evaluation script
↓
performance summary
↓
FastAPI metrics endpoint
↓
Prometheus
↓
Grafana
~~~

Understanding that chain makes debugging much easier.

## Future improvements

A larger project could add:

- alerts,
- per-service resource metrics,
- data freshness,
- queue depth,
- prediction distribution drift,
- SLO panels.

The workshop dashboard intentionally starts with a small set that tells a coherent story.
