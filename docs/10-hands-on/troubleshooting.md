# Troubleshooting

Debug the smallest failing boundary first.

## TLC base URL shows AccessDenied

That is expected for directory listing. Use the bootstrap script or an exact monthly file object.

~~~bash
uv run python scripts/bootstrap_data.py
~~~

## Wrong Python

~~~bash
uv run python --version
~~~

Expected: Python 3.11.x.

## ModuleNotFoundError

Core:

~~~bash
uv sync
~~~

Airflow:

~~~bash
uv sync --group airflow
~~~

Docs:

~~~bash
uv sync --group docs
~~~

## Snapshot missing

~~~bash
uv run dvc repro create_training_snapshot
~~~

Make sure the feature dataset exists first.

## FastAPI 503

Meaning: API process is alive but champion cannot be resolved.

Check MLflow, registered model, champion alias, and MLFLOW_TRACKING_URI.

## Switched to Docker and model disappeared

Use the shared helper:

~~~bash
uv run python scripts/start_mlflow.py
~~~

Local and Docker modes then share .mlflow state.

Stop the local server before Compose to avoid port 5000 conflict.

## FastAPI 422

Usually incomplete 168-hour demand history or an invalid target time.

## Port already in use

Common ports:

~~~text
3000 Grafana
5000 MLflow
8000 FastAPI
8080 Airflow
9090 Prometheus
~~~

Stop the process/container currently using the port.

## Airflow DAG missing

Check:

~~~bash
uv run --group airflow airflow dags list
~~~

A missing DAG is usually a parse/import problem.

## Airflow task failed

Open the failed task log and ask which input/dependency failed.

Avoid debugging the entire stack at once.

## Prometheus target down

Open:

~~~text
http://localhost:9090/targets
~~~

The API target should be reachable as api:8000 from inside Compose.

## Grafana empty

Check in order:

1. API traffic succeeded;
2. /metrics has taxi metrics;
3. Prometheus target is UP;
4. Prometheus query returns data;
5. Grafana datasource is healthy.

## CI branch policy fails

Allowed:

~~~text
feat/*, fix/*, docs/*, chore/* → develop
develop → main
~~~

## Windows issues

WSL2 is usually smoother for the Docker + Airflow portion. Avoid mixing multiple Python environments without knowing which one owns the files and commands.
