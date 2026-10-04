# Step 5 — Airflow Orchestration

## Goal

See how manual scripts become an observable dependency graph.

Do not treat Airflow as “magic automation”. Every task should map to logic you already understand.

## 1. Install Airflow group

~~~bash
uv sync --group airflow
~~~

## 2. Start Airflow

~~~bash
uv run --group airflow python scripts/start_airflow.py
~~~

Open:

~~~text
http://localhost:8080
~~~

The standalone command creates local Airflow state and local authentication.

## 3. Find the DAGs

You should see:

~~~text
taxi_daily_replay
taxi_initial_training
taxi_model_monitoring
~~~

If a DAG is missing, that is a DAG parsing problem, not a model problem.

## 4. Open taxi_daily_replay

Look at Graph view.

You should see:

~~~text
get_replay_date
      ↓
release_batch
      ↓
validate_batch
      ↓
aggregate_demand
      ↓
rebuild_features
~~~

Compare that graph with the manual scripts from earlier.

This is the key learning moment:

> Airflow did not replace the business logic. It organized it.

## 5. Trigger Jan 27

Use replay_date:

~~~text
2025-01-27
~~~

Watch task states change.

A successful run should eventually produce:

~~~text
data/raw/trips/2025-01-27.parquet
data/processed/demand/2025-01-27.parquet
~~~

and rebuild the feature dataset.

## 6. Inspect task logs

Click a task and open logs.

If a task fails, read that task's log first.

Avoid the beginner debugging pattern:

> “Airflow broken.”

Be specific:

> “validate_batch failed because the batch timestamp was wrong.”

Specific failure boundaries are one reason orchestration is useful.

## 7. Trigger the next date

Try:

~~~text
2025-01-28
~~~

Now the feature history extends further.

## 8. Understand XCom

TaskFlow may pass small result dictionaries such as:

~~~text
date
rows
path
status
~~~

The Parquet data itself stays in files.

Do not use XCom as a giant DataFrame transport.

## 9. Initial training DAG

Open:

~~~text
taxi_initial_training
~~~

See:

~~~text
snapshot
→ train
→ register candidate
~~~

This is a different lifecycle from daily data processing.

## Checkpoint

You should be able to explain:

- DAG,
- task,
- dependency,
- XCom,
- why business logic lives in src,
- why we have more than one DAG.

Next: serve champion through FastAPI.
