# Airflow Pipeline in This Project

## Manual first, orchestration second

Before this page, you should understand the manual scripts.

Airflow then coordinates those same logical steps.

## Daily replay DAG

File:

~~~text
dags/taxi_daily_replay.py
~~~

Flow:

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

### get_replay_date

Reads the date parameter supplied when triggering the DAG.

Why make it a parameter?

Because the workshop can replay different historical dates without changing Python source code.

### release_batch

Calls reusable logic that materializes one day into:

~~~text
data/raw/trips/YYYY-MM-DD.parquet
~~~

### validate_batch

Checks the daily input before transformation.

Examples:

- not empty,
- timestamps valid,
- correct date,
- pickup zone present.

This illustrates an important pattern:

~~~text
ingest
↓
validate
↓
transform
~~~

Do not let bad input quietly travel deeper into the pipeline.

### aggregate_demand

Converts individual trips into zone-hour counts.

### rebuild_features

Rebuilds the feature dataset using history through the latest replay date.

## Initial training DAG

File:

~~~text
dags/taxi_initial_training.py
~~~

Flow:

~~~text
create_snapshot
      ↓
train_model
      ↓
register_candidate
~~~

The training task logs experiments to MLflow.

The registration task only registers the candidate if it beats the naive baseline.

## Monitoring DAG

File:

~~~text
dags/taxi_model_monitoring.py
~~~

Flow:

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

The second task can become a no-op when the model is healthy.

That is a useful pattern: a task may decide there is no work to perform after evaluating state.

## Why not one giant DAG?

Because the lifecycles have different reasons to run.

~~~text
daily data flow
→ new data arrived

initial training
→ establish first model

monitoring
→ evaluate production behavior
~~~

If we placed everything in one DAG, we might accidentally teach that every daily batch must retrain the model.

That is not the behavior we want.

## How to inspect DAGs

Start Airflow:

~~~bash
uv sync --group airflow
uv run --group airflow python scripts/start_airflow.py
~~~

Open:

~~~text
http://localhost:8080
~~~

Look at:

- Graph view,
- task state,
- task logs,
- run parameters.

The graph is one of the best ways to connect the code with the mental model.

## What belongs in XCom?

Small metadata:

~~~text
rows
path
date
run_id
MAE
~~~

What stays outside:

~~~text
full DataFrame
large parquet
model artifact
~~~

Airflow coordinates references; storage systems hold large data.
