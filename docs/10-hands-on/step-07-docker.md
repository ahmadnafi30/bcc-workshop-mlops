# Step 7 — Docker and Docker Compose

## Goal

Move from separate local processes into a reproducible multi-service local stack.

## Before starting

Stop local MLflow, FastAPI, and Airflow processes with Ctrl+C. Docker Compose wants the same host ports.

## MLflow continuity

Both local MLflow and the Docker MLflow service use:

~~~text
.mlflow/
~~~

So your experiments and registry state can survive the transition from local mode to Compose mode.

## 1. Build and start

~~~bash
docker compose up -d --build
~~~

The first build can take a while, especially the Airflow image.

## 2. Check services

~~~bash
docker compose ps
~~~

Expected long-running services:

~~~text
mlflow
api
airflow
prometheus
grafana
~~~

## 3. Open interfaces

| Service | URL |
| --- | --- |
| MLflow | http://localhost:5000 |
| Airflow | http://localhost:8080 |
| FastAPI | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

## 4. Verify registry state

Open MLflow and confirm the champion still exists.

Then open:

~~~text
http://localhost:8000/model-info
~~~

If it returns champion metadata, local-to-container state continuity is working.

## 5. Understand addresses

From your browser:

~~~text
localhost:5000
~~~

From another Compose container:

~~~text
mlflow:5000
~~~

The service is the same, but the network perspective is different.

## 6. Logs

~~~bash
docker compose logs -f
~~~

One service:

~~~bash
docker compose logs -f api
~~~

## 7. Workspace

One-off project command:

~~~bash
docker compose run --rm workspace python scripts/doctor.py
~~~

Workspace is a tool container, not a long-running service.

## 8. Stop

Keep state:

~~~bash
docker compose down
~~~

Remove named volumes too:

~~~bash
docker compose down -v
~~~

The second command resets Airflow, Prometheus, and Grafana local volume state. The bind-mounted .mlflow folder is separate.

## Checkpoint

Explain image vs container, localhost vs service name, and bind mount vs named volume.
