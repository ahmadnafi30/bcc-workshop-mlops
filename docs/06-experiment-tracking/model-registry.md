# MLflow Model Registry

## Tracking and Registry are different

Tracking answers:

> What experiments did we run?

Registry answers:

> Which model versions are candidates for use?

Think of:

~~~text
experiment notebook
vs
approved model catalog
~~~

## Register a run

After tracked training, take the model run ID:

~~~bash
uv run python scripts/register_model.py --run-id <RUN_ID>
~~~

The model becomes a registered version.

Example:

~~~text
taxi-demand-forecasting-model
└── version 1
~~~

A new registration creates another version:

~~~text
version 1
version 2
version 3
~~~

## Aliases

We use:

~~~text
challenger
champion
~~~

### challenger

A candidate we want to evaluate.

### champion

The model selected for serving.

Aliases are pointers.

~~~text
champion
   ↓
version 3
~~~

Later:

~~~text
champion
   ↓
version 5
~~~

The application still asks for champion.

## Why aliases are useful

Bad serving code:

~~~text
load model version 3
~~~

Every promotion requires application code changes.

Better:

~~~text
load champion
~~~

Now model governance can change the pointer without hard-coding a new version.

## Promotion

Promotion is explicit:

~~~bash
uv run python scripts/promote_model.py --version 1
~~~

Why not automatically promote every new model?

Because:

~~~text
new
≠
approved
~~~

The workshop automates challenger creation but keeps the final production choice visible.

## Lineage

A model version keeps a source run ID.

So we can trace:

~~~text
champion alias
   ↓
model version
   ↓
MLflow run
   ↓
metrics + params + dataset fingerprint
~~~

That traceability is one of the strongest reasons to use a registry.

## Rollback idea

If a newly promoted model behaves badly, an alias can be moved back to an older version.

That gives a simple mental model for rollback:

~~~text
change pointer
not application code
~~~
