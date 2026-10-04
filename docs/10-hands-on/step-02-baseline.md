# Step 2 — Features and Baseline Model

## Goal

Build a model-ready dataset, then train a baseline and the first ML model before adding MLOps tooling.

## Why model first?

MLOps without an ML workflow is abstract.

We want to feel the pain first:

~~~text
which model?
which metric?
which data?
which artifact?
~~~

Then DVC and MLflow have a clear purpose.

## 1. Build features

~~~bash
uv run python scripts/build_features.py
~~~

Output:

~~~text
data/features/taxi_demand_features.parquet
~~~

The dataset contains:

~~~text
calendar features
lag features
rolling features
target_trip_count
~~~

## 2. Think about leakage

For a target hour, ask:

> Could I have known this value before the target hour started?

Allowed:

~~~text
lag_1h
lag_24h
calendar hour
~~~

Not allowed:

~~~text
actual target demand
future demand
rolling window containing target demand
~~~

## 3. Build the initial training snapshot manually

Before DVC orchestration, you can create it directly:

~~~bash
uv run python scripts/create_training_snapshot.py --cutoff-date 2025-01-26
~~~

Output:

~~~text
data/snapshots/training/taxi_demand_2025-01-26.parquet
~~~

## 4. Train

~~~bash
uv run python scripts/train_model.py
~~~

The script compares:

~~~text
naive 24h
vs
HistGradientBoostingRegressor
~~~

## 5. Read the result

You should see MAE and RMSE.

Do not immediately celebrate the ML model.

Ask:

~~~text
Did it beat the naive baseline?
By how much?
Is the result plausible?
~~~

## 6. Why naive 24h is useful

Taxi demand often has daily repetition.

A simple yesterday-same-hour rule can be surprisingly competitive.

That makes it a meaningful baseline instead of a deliberately terrible one.

## 7. Local output

Manual training may write:

~~~text
models/taxi_demand_model.joblib
models/initial_metrics.json
~~~

The folder is created at runtime and ignored by Git.

Later MLflow becomes the better place to manage model artifacts.

## Checkpoint

You should be able to explain:

- what target_trip_count means,
- why lag_168h needs one-week history,
- why the split is chronological,
- whether the ML model beat the baseline.

Next: make the dataset input reproducible with DVC.
