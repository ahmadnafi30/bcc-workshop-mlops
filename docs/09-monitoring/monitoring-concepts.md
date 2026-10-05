# Monitoring Concepts

## Two health questions

An ML system has at least two different health dimensions.

### System health

~~~text
Is the API alive?
Is it slow?
Are requests failing?
How much traffic is arriving?
~~~

### Model health

~~~text
Are predictions still accurate?
Which model version is serving?
Is recent MAE getting worse?
Should we retrain?
~~~

A fast API can serve a bad model.

A good model can sit behind a broken API.

We need both views.

## Analogy: delivery restaurant

Operational monitoring asks:

> Is the kitchen open? Are orders delayed?

Model monitoring asks:

> Does the food still taste good?

Both matter, but they measure different things.

## Delayed ground truth

For target 18:00:

~~~text
before 18:00
prediction exists

after 18:00
actual demand becomes available
~~~

We cannot know prediction error before the actual outcome exists.

So we log predictions first, evaluate them later.

## Prediction log

Stored as JSONL:

~~~text
data/monitoring/predictions.jsonl
~~~

Important fields:

- zone,
- target time,
- prediction,
- model version,
- run ID.

## Evaluation table

When ground truth becomes available:

~~~text
prediction
+
processed actual demand
↓
absolute error
squared error
~~~

Output:

~~~text
data/monitoring/evaluations.parquet
~~~

## Performance summary

The project writes:

~~~text
data/monitoring/performance_summary.json
~~~

It contains values such as:

- recent MAE,
- recent RMSE,
- reference MAE,
- threshold MAE,
- number of evaluated predictions,
- retraining recommendation.

## Reference performance

We do not choose an arbitrary fixed number such as:

~~~text
if MAE > 20
~~~

Instead we compare against the champion's validation MAE from MLflow.

Example:

~~~text
champion validation MAE = 10
multiplier = 1.25

threshold = 12.5
~~~

This makes the threshold relative to known model quality.

## Minimum sample

We also require enough evaluated predictions.

Why?

A single weird hour should not immediately cause retraining.

Monitoring decisions should look for a pattern, not panic over one outlier.

## Drift vs performance degradation

This workshop directly monitors performance degradation using ground truth.

Data drift is related but different.

~~~text
data drift
→ input distribution changed

performance degradation
→ prediction error got worse
~~~

Drift can happen without accuracy loss, and accuracy can degrade for reasons beyond simple feature distribution drift.

A future extension could add Evidently or custom drift metrics.
