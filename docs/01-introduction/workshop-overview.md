# Workshop Overview

## What are we actually learning?

This workshop is not a tour of random tools.

We start from a working ML problem, then introduce each tool when a real pain appears.

That gives us a much better learning sequence than:

~~~text
install Docker
install Airflow
install MLflow
good luck
~~~

## Audience

You should be comfortable with:

- basic Python,
- Pandas,
- train and validation concepts,
- regression metrics such as MAE,
- basic Git commands.

You do not need previous experience with the MLOps tools in this repository.

## Learning outcomes

After finishing, you should be able to explain:

1. why training a model is only one part of an ML system;
2. how code, data, experiments, and models can be traced;
3. how workflows become repeatable;
4. how a model becomes an API;
5. why containers help reproducibility;
6. what CI/CD means in an ML project;
7. the difference between system monitoring and model monitoring;
8. how evidence can trigger retraining.

You do not need to memorize every YAML file.

## Why taxi demand?

Taxi demand naturally gives us:

- time,
- location,
- repeating patterns,
- changing behavior,
- delayed ground truth,
- regression metrics,
- a reason to monitor and retrain.

Example:

~~~text
17:00
predict 18:00 demand

18:00–18:59
real trips happen

after the hour
actual demand becomes available

prediction vs actual
→ calculate error
~~~

That delayed ground truth is very useful for explaining production ML.

## Workshop stages

### Data

We download NYC TLC data and transform trip-level records into hourly Manhattan zone demand.

### Baseline ML

Before MLOps, we create:

- a naive 24-hour baseline,
- HistGradientBoostingRegressor,
- MAE and RMSE.

This gives the MLOps tools something real to manage.

### DVC

We freeze the exact training snapshot.

Question answered:

> “Which data produced this model?”

### MLflow

We track parameters, metrics, dataset fingerprint, and the model artifact.

Question answered:

> “What happened in this experiment?”

### Model Registry

We introduce model versions and the aliases **challenger** and **champion**.

Question answered:

> “Which model is approved for serving?”

### Airflow

We describe dependencies and task order.

Question answered:

> “What runs after what, and what happens if a task fails?”

### FastAPI

The model gets an HTTP interface.

Question answered:

> “How does another application ask for a prediction?”

### Docker

We package runtime environments.

Question answered:

> “How do we reduce 'works on my laptop' differences?”

### GitHub Actions

We automate tests, linting, docs checks, Docker builds, and container delivery.

Question answered:

> “How do we verify changes consistently?”

### Prometheus + Grafana

We observe API and model metrics.

Question answered:

> “How do we know the deployed system is healthy?”

### Retraining

We compare recent MAE against champion validation MAE.

Question answered:

> “When should we create a new candidate model?”

## What is intentionally out of scope?

We do not deeply cover:

- Kubernetes,
- cloud IAM,
- Kafka,
- feature stores,
- Terraform,
- distributed training,
- deep time-series foundation models.

Those are good next topics after the lifecycle is clear.
