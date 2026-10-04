# Apache Airflow

## Why Airflow appears in this project

Before Airflow, our scripts already work.

We can manually run:

~~~text
release data
validate
aggregate
build features
train
evaluate
~~~

That is intentional.

An orchestrator should coordinate working logic, not become the only place where the logic exists.

Airflow solves a different problem:

> What should run, in what order, when, and what happens if something fails?

## Analogy: a film production schedule

Imagine making a film.

You have teams for:

- lighting,
- camera,
- actors,
- editing.

The schedule does not do the camera operator's job.

It says:

~~~text
set ready
   ↓
lighting ready
   ↓
camera starts
   ↓
actors perform
   ↓
editing receives footage
~~~

Airflow is closer to the production schedule.

The real domain work remains in Python functions.

## What is a DAG?

DAG means:

> Directed Acyclic Graph

Break the words down.

### Graph

A graph has nodes and relationships.

In Airflow:

~~~text
node
→ task

edge
→ dependency
~~~

### Directed

The relationship has direction.

~~~text
validate
   ↓
aggregate
~~~

means aggregate depends on validate.

Not the reverse.

### Acyclic

The dependency graph cannot loop forever.

Bad:

~~~text
A → B → C → A
~~~

A workflow needs a valid execution order.

## A simple DAG

~~~text
download
   ↓
validate
   ↓
transform
   ↓
save
~~~

If validate fails, transform should not blindly continue.

That dependency is one of the most important reasons to use an orchestrator.

## DAG file vs business logic

Our rule:

~~~text
dags/
→ WHEN + IN WHAT ORDER

src/
→ HOW
~~~

Bad pattern:

~~~python
@task
def preprocess():
    # 300 lines of pandas logic here
~~~

Better:

~~~python
@task
def preprocess():
    return reusable_preprocess_function(...)
~~~

Why?

Because reusable logic becomes:

- easier to test,
- callable without Airflow,
- easier to explain,
- less coupled to orchestration.

## TaskFlow API

Airflow 3 exposes stable authoring interfaces from airflow.sdk.

We use decorators such as:

~~~python
@dag(...)
def my_pipeline():

    @task
    def first_task():
        ...

    @task
    def second_task(value):
        ...

    result = first_task()
    second_task(result)
~~~

Something subtle happens here.

When Airflow parses the DAG, calling first_task does not immediately execute the business code like a normal Python function call.

It creates task relationships for the workflow.

## XCom

TaskFlow can pass small return values between tasks using XCom.

Example:

~~~text
release_batch
returns:
{
  date,
  rows,
  path
}

next task
receives that metadata
~~~

XCom is good for small metadata.

We deliberately do **not** pass a full DataFrame through XCom.

Why?

Airflow's metadata system is not a large-data transport layer.

Large data stays in files:

~~~text
data/raw
data/processed
data/features
~~~

Tasks exchange references and summaries.

## Our DAGs

### taxi_daily_replay

~~~text
get_replay_date
      ↓
release_batch
      ↓
validate_batch
      ↓
aggregate_demand
      ↓
rebuild_features
~~~

Purpose:

> simulate one new production day arriving.

### taxi_initial_training

~~~text
create_snapshot
      ↓
train_model
      ↓
register_candidate
~~~

Purpose:

> produce an initial challenger from a reproducible snapshot.

### taxi_model_monitoring

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Inside maybe_retrain:

~~~text
healthy
→ stop

degraded
→ new snapshot
→ retrain
→ register challenger
~~~

## How to make a DAG from zero

A useful design sequence is:

### Step 1 — write the workflow in plain language

Example:

~~~text
receive file
validate file
aggregate data
build features
~~~

### Step 2 — identify task boundaries

Ask:

> If this fails, do I want to know which step failed?

That often reveals useful task boundaries.

### Step 3 — identify dependencies

~~~text
validate requires received file
aggregate requires valid file
features require aggregated demand
~~~

### Step 4 — keep heavy logic in src/

Write reusable Python functions first.

### Step 5 — connect tasks in the DAG

Now the DAG is mostly orchestration.

## schedule=None

Our workshop DAGs are manually triggered.

Why?

Historical replay lets us simulate Jan 27, Jan 28, and Jan 29 within minutes.

A real deployment may use a schedule.

The workshop keeps manual triggers so participants can see each lifecycle step clearly.

## Idempotency

A good pipeline should handle reruns predictably.

For example, releasing the same historical date should not silently duplicate data.

Our scripts and orchestration check existing outputs or rebuild deterministic outputs where appropriate.

Idempotency is a useful production habit:

> rerunning the same logical work should not randomly corrupt state.

## Debugging Airflow

Useful questions:

1. Did the DAG parse?
2. Which task failed?
3. What was the task log?
4. Did the input file exist?
5. Was MLflow reachable?
6. Did a previous upstream task actually produce the expected artifact?

Do not debug the whole DAG as one giant object.

Debug the failed task and its dependency.

## Airflow vs GitHub Actions

This distinction matters.

~~~text
Airflow
→ orchestrates data / ML workflows

GitHub Actions
→ reacts to code repository events
~~~

Examples:

~~~text
new taxi batch
→ Airflow

new pull request
→ GitHub Actions
~~~

They can interact, but they solve different trigger problems.

## Takeaway

Airflow is not “a place to put Python code”.

Airflow is a system for making workflow dependencies visible, schedulable, observable, and repeatable.
