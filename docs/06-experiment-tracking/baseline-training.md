# Baseline Training

## Why train manually before MLflow?

If we install MLflow before we have an experiment, the tool feels abstract.

So first we run a plain ML workflow.

## Models

### Naive 24-hour baseline

~~~text
prediction(t) = demand(t - 24h)
~~~

No fitting required.

### HistGradientBoostingRegressor

Uses:

- zone category,
- calendar features,
- lag features,
- rolling features.

## Run

After data and features:

~~~bash
uv run python scripts/train_model.py
~~~

The script:

1. loads the training snapshot;
2. creates chronological train/validation split;
3. evaluates naive baseline;
4. trains gradient boosting;
5. evaluates the model;
6. saves local artifacts.

## Why compare against a naive rule?

Because sophistication is not automatically value.

If:

~~~text
ML model MAE = 15
baseline MAE = 10
~~~

then the simple baseline is currently better.

That is valuable information.

## Time split

The validation data happens after training data.

This better resembles how the model will encounter future observations.

Random row splitting is often a bad default for time-dependent forecasting problems.

## Local artifacts

Manual training can create:

~~~text
models/taxi_demand_model.joblib
models/initial_metrics.json
~~~

They are local generated artifacts and are ignored by Git.

Later, MLflow becomes the system of record for experiment artifacts.

## What should you inspect?

After the run:

- training row count,
- validation row count,
- baseline MAE,
- model MAE,
- RMSE,
- whether the model beats baseline.

Do not only ask “did the script finish?”

Ask whether the result makes sense.
