# Step 4 — MLflow Tracking and Registry

## Goal

Track experiments, then move a good run into a model registry.

This step has two concepts:

~~~text
Tracking
→ record experiments

Registry
→ manage model versions selected for use
~~~

## 1. Start MLflow

Open a terminal:

~~~bash
uv run mlflow server
~~~

Keep it running.

Open:

~~~text
http://127.0.0.1:5000
~~~

## 2. Run tracked training

In another terminal:

~~~bash
uv run python scripts/train_with_mlflow.py
~~~

The script logs:

~~~text
naive-24h
hist-gradient-boosting
~~~

## 3. Explore a run

In MLflow UI, open the gradient boosting run.

Find:

- parameters,
- MAE,
- RMSE,
- dataset snapshot name,
- dataset SHA256,
- model artifact,
- tags.

Ask yourself:

> If I return next month, can this page explain what happened?

That is the point of experiment tracking.

## 4. Compare runs

Compare baseline and model.

The ML model should justify its added complexity.

## 5. Copy the model run ID

The terminal prints the tracked model run ID.

Use it:

~~~bash
uv run python scripts/register_model.py --run-id <RUN_ID>
~~~

## 6. Open Model Registry

Find:

~~~text
taxi-demand-forecasting-model
~~~

You should see a version with alias:

~~~text
challenger
~~~

## 7. Why challenger first?

New does not mean approved.

The model is a candidate.

## 8. Promote

After reviewing the model version:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

Now the selected version also has:

~~~text
champion
~~~

## 9. Understand the pointer

Serving code will ask for:

~~~text
champion
~~~

not:

~~~text
version 1 forever
~~~

That lets the model lifecycle change independently from API source code.

## Checkpoint

In MLflow you should be able to trace:

~~~text
champion
   ↓
model version
   ↓
source run
   ↓
metric + params + dataset fingerprint
~~~

Next: let Airflow coordinate repeated workflows.
