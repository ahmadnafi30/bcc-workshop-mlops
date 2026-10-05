# Step 6 — FastAPI Serving

## Goal

Use the champion model through HTTP instead of calling the Python model object directly.

## 1. Start shared local MLflow

~~~bash
uv run python scripts/start_mlflow.py
~~~

The helper uses the local .mlflow directory, the same state directory later mounted by Docker Compose.

## 2. Check champion

Open MLflow at:

~~~text
http://127.0.0.1:5000
~~~

The registered model should have a champion alias. If not:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

## 3. Make sure historical demand exists

For a Jan 28 target, processed history must cover the required 168-hour lookback before the target hour.

If you followed the Airflow section, replay Jan 27 and Jan 28 first.

## 4. Start FastAPI

~~~bash
uv run uvicorn api.main:app --reload
~~~

Swagger:

~~~text
http://127.0.0.1:8000/docs
~~~

## 5. Health check

~~~bash
curl http://127.0.0.1:8000/health
~~~

Expected:

~~~json
{"status": "ok"}
~~~

Health only answers whether the API process is alive. It does not prove the model registry is ready.

## 6. Model info

~~~bash
curl http://127.0.0.1:8000/model-info
~~~

Look for model name, version, alias, run ID, and model URI.

This endpoint answers:

> Which model is the API actually using?

## 7. Prediction

POST in Swagger:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Internal flow:

~~~text
request
   ↓
validation
   ↓
load past demand
   ↓
online features
   ↓
resolve champion
   ↓
predict
   ↓
prediction log
   ↓
response
~~~

## 8. Read more than the prediction

The response also contains model_version, model_alias, and run_id.

Those fields give us prediction lineage.

## Common errors

### 503

API is alive, but champion cannot be resolved. Check MLflow and the registry alias.

### 422

The request cannot be turned into a valid prediction. Common causes are incomplete history or a target time that is not exactly on the hour.

## Checkpoint

You should be able to explain why the client sends zone and target time instead of internal lag features.
