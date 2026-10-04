# MLOps from Zero

## Start from a normal ML project

A simple ML project might look like:

~~~text
notebook.ipynb
dataset.csv
model.pkl
~~~

For experimentation, that is fine.

The difficulty starts when the model becomes something other people depend on.

## Restaurant analogy

Think of the model as a recipe.

| Restaurant | ML system |
| --- | --- |
| recipe | model code |
| ingredients | data |
| ingredient batch | dataset version |
| kitchen process | training pipeline |
| cooking log | experiment tracking |
| approved menu item | registered model |
| waiter | prediction API |
| kitchen environment | container |
| manager schedule | orchestrator |
| quality dashboard | monitoring |
| update recipe | retraining |

The main lesson:

> **A model is a component, not the whole system.**

## Practical definition

For this workshop:

> MLOps is the set of practices that make an ML lifecycle reproducible, deployable, observable, and maintainable.

### Reproducible

Can we recreate the result later?

We need to know:

- code version,
- data version,
- parameters,
- runtime environment.

### Deployable

Can another application actually use it?

We need:

- a stable artifact,
- a serving interface,
- a predictable runtime.

### Observable

Can we see what is happening?

Examples:

- request count,
- API latency,
- current model version,
- recent MAE.

### Maintainable

Can the system safely change?

Examples:

- automated checks,
- challenger models,
- retraining,
- rollback.

## Why Git alone is not enough

Traditional software behavior mostly comes from code.

ML behavior comes from:

~~~text
code
+
data
+
parameters
+
model artifact
~~~

Two people can run the same Git commit with different training data and get different models.

Git remains essential, but data and experiment lineage need additional handling.

## Why experiment tracking exists

Imagine:

~~~text
run A → MAE 14.2
run B → MAE 11.7
run C → MAE 12.0
~~~

Then someone asks:

- Which dataset was run B using?
- What was the learning rate?
- Where is the model file?
- Which run became production?

That bookkeeping is exactly where experiment tracking becomes useful.

## Why orchestration exists

A repeated workflow might be:

~~~text
new data
  ↓
validate
  ↓
aggregate
  ↓
features
  ↓
train
  ↓
evaluate
~~~

You can run this manually once.

Repeated execution is where ordering, retries, visibility, and failure handling become important.

Airflow manages the workflow. It does not make the model smarter.

## Why ML monitoring is special

A normal web service asks:

- Is it alive?
- Is it slow?
- Are requests failing?

An ML system also asks:

- Are predictions still accurate?

That answer can be delayed.

~~~text
prediction now
+
ground truth later
=
model performance
~~~

That is why prediction logging and delayed evaluation matter.

## MLOps is not a tool checklist

Installing Docker, Airflow, and MLflow does not automatically create good MLOps.

The important practices are:

- reproducibility,
- traceability,
- automation,
- observability,
- safe model lifecycle management.

Tools are implementation choices.
