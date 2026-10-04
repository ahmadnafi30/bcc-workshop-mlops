# DVC — Data Version Control

## The problem before DVC

Imagine this folder:

~~~text
taxi_demand_features.parquet
~~~

You train model version 1.

A week later, new rows are added to the same file and you train model version 2.

Then someone asks:

> Which exact dataset produced model version 1?

The filename is the same.

Git commit history alone does not tell us the content of a large generated Parquet file.

That is the problem DVC helps us organize.

## Analogy: Git for a recipe, DVC for the ingredient batch

Git is great for:

- code,
- configuration,
- documentation.

DVC is useful for describing and reproducing data pipeline outputs.

Think about a bakery:

~~~text
Git
→ which recipe version?

DVC
→ which flour batch / prepared ingredient snapshot?

MLflow
→ what result did the baking experiment produce?
~~~

Those tools answer different questions.

## What do we version in this workshop?

We focus on the data closest to model training:

~~~text
data/snapshots/training/taxi_demand_2025-01-26.parquet
~~~

Why not every raw TLC file?

The official raw data can be downloaded again. For model reproducibility, the most important teaching artifact is the **exact model-ready snapshot** used by training.

A larger production project may also version raw and intermediate datasets.

## dvc.yaml

Open:

~~~text
dvc.yaml
~~~

You will see a stage called:

~~~text
create_training_snapshot
~~~

A DVC stage has three ideas:

~~~text
cmd
→ what command creates the result?

deps
→ what inputs affect the result?

outs
→ what output is produced?
~~~

Our dependency graph is conceptually:

~~~text
feature parquet
      +
snapshot code
      +
snapshot script
      ↓
create_training_snapshot
      ↓
training snapshot parquet
~~~

## Run the stage

~~~bash
uv run dvc repro create_training_snapshot
~~~

DVC checks dependencies and decides whether the stage needs to run again.

Analogy:

> If the ingredients and recipe have not changed, do we really need to cook the same intermediate result again?

That is why DVC feels similar to a build system.

## dvc.lock

After reproduction, DVC can create a lock file containing checksums that describe the resolved pipeline state.

Do not confuse:

~~~text
uv dependency lock
vs
DVC pipeline lock
~~~

They solve different reproducibility problems.

## DVC cache

DVC stores data content in a local cache.

~~~text
.dvc/cache
~~~

That cache is ignored by Git.

Git stores the lightweight metadata; the heavy data stays outside normal Git history.

## Why no DVC remote yet?

A team normally wants shared storage such as S3 or another supported remote.

For the workshop, a local cache is enough to understand:

- dependency tracking,
- output tracking,
- reproducibility,
- relationship between Git and data state.

Adding cloud credentials would distract from the core concept.

## Relationship with MLflow

During training we also calculate a SHA256 fingerprint for the snapshot.

MLflow stores metadata such as:

~~~text
dataset_snapshot
dataset_sha256
dataset_rows
dataset_zones
~~~

So a model run can point back to the dataset identity.

Mental model:

~~~text
DVC
→ reproduce the data artifact

MLflow
→ explain what training run used it
~~~

## Common mistakes

### Tracking huge data directly with Git

Git repositories become unnecessarily heavy.

### Thinking DVC replaces Git

It does not. DVC is designed to work with source control, not eliminate it.

### Editing a snapshot after training

A training snapshot should behave like a frozen input. Make a new snapshot for a new training cycle.

## Checkpoint

After running the DVC stage, verify:

~~~text
data/snapshots/training/
└── taxi_demand_2025-01-26.parquet
~~~

Then continue to model training and MLflow.
