# MLflow Experiment Tracking

## The problem

A few experiments are easy to remember.

Twenty experiments are not.

Imagine notes like:

~~~text
model A maybe lr .05?
dataset new?
MAE 11-ish
~~~

That is not reproducible experiment history.

MLflow Tracking gives each run structured metadata.

## Analogy: laboratory notebook

A scientist records:

- experiment conditions,
- measurement,
- sample,
- result.

MLflow does the same for ML experiments.

## Start MLflow

~~~bash
uv run mlflow server
~~~

Open:

~~~text
http://127.0.0.1:5000
~~~

## Run tracked training

~~~bash
uv run python scripts/train_with_mlflow.py
~~~

Two runs are logged:

~~~text
naive-24h
hist-gradient-boosting
~~~

## What is stored?

Parameters:

~~~text
model_type
learning_rate
max_iter
dataset_snapshot
dataset_sha256
train_rows
validation_rows
~~~

Metrics:

~~~text
mae
rmse
~~~

Tags:

~~~text
task
model_family
stage
~~~

Model artifact:

~~~text
MLflow sklearn model
~~~

## Parameter vs metric

Useful distinction:

~~~text
parameter
→ input / configuration

metric
→ measured result
~~~

Example:

~~~text
learning_rate
→ parameter

mae
→ metric
~~~

## Run ID

Each experiment run gets a unique ID.

That ID becomes important for model lineage.

A registered model version can point back to the exact run that produced it.

## Dataset fingerprint

We log SHA256 and snapshot metadata so the run records its training data identity.

This connects:

~~~text
DVC/data snapshot
↓
MLflow run
↓
model artifact
~~~

## Why track baseline too?

Because experiment tracking should preserve the comparison context.

If only the fancy model is logged, we lose the evidence that justified using it.

## What to explore in the UI

Open a run and find:

- Parameters,
- Metrics,
- Tags,
- Artifacts,
- model signature / input example.

Then compare runs side by side.

That UI exploration is part of the workshop, not decoration.
