# Architecture

## Big picture

~~~text
NYC TLC source
      ↓
bootstrap / historical replay
      ↓
hourly zone demand
      ↓
feature engineering
      ↓
DVC snapshot
      ↓
model training
      ↓
MLflow tracking
      ↓
Model Registry
      ↓
FastAPI
      ↓
prediction log
      ↓
ground truth evaluation
      ↓
monitoring
      ↓
retraining → challenger
~~~

Airflow orchestrates repeated workflow steps. Docker Compose runs local services. GitHub Actions validates and packages changes.

## Three layers

### Data layer

~~~text
trip records
    ↓
hourly demand
    ↓
features
    ↓
training snapshot
~~~

Question:

> What data does the model learn from?

### Model lifecycle

~~~text
snapshot
   ↓
train
   ↓
evaluate
   ↓
track
   ↓
register
   ↓
promote
   ↓
serve
~~~

Question:

> How does an experiment become the model used by the application?

### Operations

~~~text
request
   ↓
API metrics
   ↓
Prometheus
   ↓
Grafana

prediction
   ↓
actual demand later
   ↓
MAE
   ↓
retraining decision
~~~

Question:

> How do we know the system is healthy after deployment?

## Folder responsibilities

### src/

Reusable business logic.

Examples:

- ingestion,
- aggregation,
- feature engineering,
- training,
- monitoring.

### scripts/

Manual entry points for humans.

Example:

~~~bash
uv run python scripts/build_features.py
~~~

Scripts should reuse src functions instead of duplicating core logic.

### dags/

Airflow workflow definitions.

A DAG should mostly explain:

~~~text
WHEN
+
IN WHAT ORDER
~~~

not hide hundreds of lines of preprocessing inside the DAG file.

### api/

HTTP concerns:

- request validation,
- response schema,
- status codes,
- dependency wiring.

Prediction logic itself remains reusable under src/serving.

## Local Docker services

~~~text
FastAPI    → mlflow:5000
Prometheus → api:8000/metrics
Grafana    → prometheus:9090
Airflow    → mlflow:5000
~~~

Docker Compose gives services DNS names based on service names.

Inside the API container, localhost means the API container itself. It does not mean MLflow.

## Storage

| Purpose | Location |
| --- | --- |
| source data | data/source |
| raw replay batch | data/raw/trips |
| processed hourly demand | data/processed/demand |
| feature dataset | data/features |
| training snapshots | data/snapshots/training |
| prediction logs | data/monitoring |
| MLflow state | Docker volume |
| Airflow state | Docker volume |
| Prometheus TSDB | Docker volume |

Generated data is ignored by Git.

## Workshop simplifications

We intentionally use:

- one machine,
- local files,
- SQLite for local tracking metadata,
- Airflow standalone,
- manual champion approval.

A larger production setup may replace those pieces without changing the lifecycle concepts.
