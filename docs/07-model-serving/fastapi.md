# FastAPI

## Why FastAPI?

FastAPI gives us a small HTTP application around prediction logic.

The project separates:

~~~text
api/
→ HTTP concerns

src/serving/
→ ML serving logic
~~~

That separation makes testing easier.

## Main files

~~~text
api/
├── main.py
├── schemas.py
└── dependencies.py
~~~

### main.py

Defines endpoints and maps Python exceptions into HTTP responses.

### schemas.py

Defines request and response shapes using Pydantic models.

### dependencies.py

Creates reusable objects such as the predictor.

## Endpoint: GET /health

Purpose:

> Is the API process alive?

Response:

~~~json
{
  "status": "ok"
}
~~~

This endpoint intentionally does not require MLflow to be healthy.

Why?

Because two questions are different:

~~~text
Is FastAPI alive?
Is the model dependency ready?
~~~

## Endpoint: GET /model-info

Purpose:

> Which registered model is currently selected by the serving alias?

Example information:

~~~text
model_name
model_version
model_alias
run_id
model_uri
~~~

If champion is missing, this endpoint can return 503.

## Endpoint: POST /predict

Request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Response contains:

~~~text
zone_id
target_datetime
predicted_trip_count
model_name
model_version
model_alias
run_id
model_uri
~~~

Including model metadata makes debugging much easier.

If someone asks:

> “Which model created this prediction?”

the response already gives us useful lineage.

## HTTP status codes in this project

### 200

Request succeeded.

### 422

The request structure may be valid JSON, but prediction cannot be built from the supplied input or available history.

Examples:

- target time is not at the start of an hour,
- required historical demand is missing.

### 503

The API process is alive, but the model dependency is not ready.

Example:

- champion alias does not exist in MLflow Registry.

## Dependency injection

FastAPI can inject reusable dependencies into endpoints.

Our predictor is created through a dependency function.

That makes tests easier because we can replace the real predictor with a fake predictor.

## Why fake dependencies in tests?

Unit tests should not require:

- a real MLflow server,
- a real registered model,
- a huge TLC dataset.

We override the dependency and test the API contract separately.

That means:

~~~text
API test
→ test HTTP behavior

serving test
→ test feature + model behavior

integration demo
→ test the real stack
~~~

Different test levels answer different questions.

## Before starting locally

Start the shared local MLflow server first:

~~~bash
uv run python scripts/start_mlflow.py
~~~

Make sure the registered model already has a `champion` alias. The API resolves that alias instead of hard-coding a model version.

## Start locally

~~~bash
uv run uvicorn api.main:app --reload
~~~

Open Swagger UI:

~~~text
http://127.0.0.1:8000/docs
~~~

Swagger is especially useful for beginners because you can inspect schemas and send requests without writing curl commands.

## Metrics endpoint

FastAPI also exposes:

~~~text
GET /metrics
~~~

Prometheus scrapes this endpoint later.

It is hidden from the main OpenAPI workshop interface because it is operational infrastructure, not a user-facing prediction API.

## Common errors

### 503 model champion unavailable

Check:

1. MLflow is running;
2. a model was registered;
3. a model version was promoted to champion;
4. MLFLOW_TRACKING_URI points to the correct server.

### 422 history missing

The model needs up to 168 hours of history.

Make sure processed demand exists for the full lookback window.
