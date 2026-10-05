# Docker Compose

## Why Compose?

We now have several services:

~~~text
FastAPI
MLflow
Airflow
Prometheus
Grafana
~~~

Starting each one manually with the correct network, port, volume, and environment variable would be annoying.

Docker Compose describes the local stack in one file:

~~~text
docker-compose.yml
~~~

## Analogy: apartment building manager

Docker images are individual apartment designs.

Compose is the building plan:

- which apartments exist,
- which ports are exposed,
- which storage they use,
- which services depend on others,
- how they find each other.

## Start everything

~~~bash
docker compose up -d --build
~~~

Break it down:

~~~text
up
→ create/start services

-d
→ detached mode

--build
→ rebuild local images first
~~~

## Service discovery

Compose creates a default network.

Services can reach each other by service name.

Examples:

~~~text
api → http://mlflow:5000
prometheus → http://api:8000/metrics
grafana → http://prometheus:9090
~~~

From your browser, you use published host ports:

~~~text
http://localhost:5000
http://localhost:8000
~~~

Internal and external addresses are different views of the same service.

## depends_on and health checks

Starting a process does not always mean it is ready.

For example:

~~~text
MLflow container started
≠
MLflow HTTP endpoint ready
~~~

Health checks let Compose wait for useful readiness before dependent services proceed.

## Persistent state

Persistent storage is split into a bind mount and named volumes.

### Shared MLflow bind mount

~~~text
./.mlflow
→ /mlflow
~~~

The local helper `scripts/start_mlflow.py` and the Docker MLflow service use the same repository-local state directory. That keeps experiment history and Model Registry state continuous when the workshop moves from local processes to Docker Compose.

### Named volumes

~~~text
airflow-home
prometheus-data
grafana-data
dvc-cache
~~~

Stopping a container does not necessarily remove those volumes.

### Stop

~~~bash
docker compose down
~~~

### Stop and delete volumes

~~~bash
docker compose down -v
~~~

The second command deletes the named volumes above. It does **not** delete the bind-mounted `.mlflow/` directory, so MLflow state remains unless you remove that folder yourself.

## Workspace service

The Compose file also has a tools profile with a workspace container.

It is useful for one-off commands:

~~~bash
docker compose run --rm workspace python scripts/bootstrap_data.py
~~~

This means a participant can execute the project logic inside the same containerized environment.

## Check the stack

~~~bash
docker compose ps
~~~

Logs:

~~~bash
docker compose logs -f
~~~

One service:

~~~bash
docker compose logs -f api
~~~

## Workshop URLs

| Service | Host URL |
| --- | --- |
| MLflow | http://localhost:5000 |
| Airflow | http://localhost:8080 |
| FastAPI | http://localhost:8000 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

## Production note

Compose is excellent for local learning and many development workflows.

A large production platform may use another orchestrator or cloud service.

The lesson here is the multi-service boundary and configuration, not “Compose is always production”.
