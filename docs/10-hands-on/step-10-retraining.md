# Step 10 — Monitoring-Driven Retraining

## Goal

Close the loop:

~~~text
monitor
→ decide
→ optional retrain
→ challenger
→ review
→ promotion
~~~

## 1. Inspect summary

Open:

~~~text
data/monitoring/performance_summary.json
~~~

Important fields:

~~~text
recent_mae
reference_mae
threshold_mae
evaluation_count
retrain_recommended
~~~

## 2. Default decision

~~~text
recent MAE > reference MAE × 1.25
and
evaluation_count >= 100
~~~

If false, no retraining is the correct result.

Automation should not manufacture work.

## 3. Trigger monitoring DAG

Open Airflow:

~~~text
http://localhost:8080
~~~

Trigger:

~~~text
taxi_model_monitoring
~~~

Default params:

~~~text
degradation_multiplier = 1.25
min_samples = 100
recent_limit = 500
~~~

## 4. Healthy path

~~~text
evaluate
   ↓
within threshold
   ↓
not_needed
~~~

That is a successful decision.

## 5. Degraded path

~~~text
latest evaluated date
      ↓
new training snapshot
      ↓
train
      ↓
latest five days validation
      ↓
MLflow
      ↓
beat baseline?
      ↓
challenger
~~~

## 6. Inspect MLflow

If retraining ran, look for stage:

~~~text
retraining-validation
~~~

Compare dataset fingerprint and validation metrics with older runs.

## 7. Inspect Registry

The new candidate may become challenger.

Champion should not move automatically.

## 8. Review and promote

If the candidate is acceptable:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

The serving layer asks for champion, so it can adopt the new approved version without hard-coding a number.

## Checkpoint

You should be able to explain why automatic retraining and automatic production promotion are separate governance decisions.
