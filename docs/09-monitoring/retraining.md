# Retraining

## Retraining should answer a reason

A weak rule is:

~~~text
retrain every day because ML
~~~

A better question is:

> What evidence says the current model needs a new candidate?

Our workshop uses recent prediction error.

## Decision rule

Default:

~~~text
recent MAE
>
champion validation MAE × 1.25
~~~

and:

~~~text
evaluated predictions >= 100
~~~

Both values are configurable.

## Why relative threshold?

Model quality depends on the task.

An MAE of 20 might be terrible for one problem and excellent for another.

Using champion validation MAE gives the threshold context.

## Why minimum sample?

One strange hour is not enough evidence.

A minimum evaluation count reduces overreaction.

## Monitoring DAG

~~~text
taxi_model_monitoring
~~~

Flow:

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

If healthy:

~~~text
stop
~~~

If degraded:

~~~text
new snapshot
    ↓
train
    ↓
validation
    ↓
MLflow
    ↓
beat baseline?
    ↓
register challenger
~~~

## Moving validation window

Initial snapshot:

~~~text
older rows → training
last 5 days → validation
~~~

A later retraining snapshot follows the same rule.

That prevents validation from staying frozen forever in January while training moves into February.

## Automatic retraining vs automatic promotion

These are different decisions.

We allow:

~~~text
monitoring
→ automatic retraining
→ automatic challenger registration
~~~

We do not automatically do:

~~~text
challenger
→ champion
~~~

Why?

Because a model can beat the naive baseline without necessarily being better than the current champion in every important way.

Manual promotion keeps governance visible in the workshop.

## Candidate review

Before promotion, inspect:

- candidate validation MAE,
- candidate RMSE,
- snapshot date,
- dataset fingerprint,
- MLflow run,
- current champion performance.

Then promote explicitly.

## Retraining is not continual learning

This project retrains a batch model from a newer snapshot.

That is different from online or continual learning where model parameters may update incrementally as data arrives.

Keeping the distinction clear prevents terminology confusion.
