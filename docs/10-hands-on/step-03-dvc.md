# Step 3 — DVC Snapshot

## Goal

Turn “I trained from some Parquet file” into a reproducible data pipeline stage.

## 1. Open dvc.yaml

Before running anything, inspect:

~~~text
dvc.yaml
~~~

Find:

~~~text
cmd
deps
outs
~~~

Try to explain them in your own words.

A useful translation:

~~~text
cmd
→ what should I run?

deps
→ what could change the result?

outs
→ what result should exist?
~~~

## 2. Reproduce the stage

~~~bash
uv run dvc repro create_training_snapshot
~~~

DVC checks whether the dependencies changed.

If needed, it executes the snapshot script.

## 3. Inspect status

~~~bash
uv run dvc status
~~~

If everything is current, DVC should not report that the stage needs reproduction.

## 4. Run again

~~~bash
uv run dvc repro create_training_snapshot
~~~

Notice that a reproducibility tool is not only about “running commands”.

It understands dependency state.

## 5. What should be in Git?

DVC metadata and pipeline definitions can be versioned.

Generated data stays outside normal Git history.

Mental model:

~~~text
Git commit
→ code + DVC metadata

DVC cache
→ heavy data content
~~~

## 6. Why this matters for models

Suppose model v1 and v2 use different snapshots.

We want lineage such as:

~~~text
model v1
→ snapshot A

model v2
→ snapshot B
~~~

This is much stronger than both models saying they came from features.parquet.

## Checkpoint

You should now be able to answer:

> Why do we need both Git and DVC?

Short answer:

~~~text
Git tracks project source state.
DVC helps track/reproduce data pipeline artifacts.
~~~

Next: log experiments with MLflow.
