# Glossary

## Artifact

A produced output stored for later use, such as a model or Docker image.

## Baseline

A simple reference method used to judge whether a more complex model helps.

## Champion

Registered model alias selected for serving.

## Challenger

Candidate registered model that may replace champion after review.

## CI

Continuous Integration: automated verification of repository changes.

## CD

Continuous Delivery or Continuous Deployment. This workshop uses delivery to GHCR.

## Container

A running instance of a container image.

## DAG

Directed Acyclic Graph: Airflow's dependency graph of tasks.

## Data leakage

Using information in a feature that would not have been available at prediction time.

## DVC

Data Version Control. Used here to define/reproduce training snapshot state.

## Feature

A model input, such as lag_24h or hour.

## Ground truth

The actual observed outcome used to evaluate an earlier prediction.

## Histogram

Prometheus metric type that collects observations in buckets, useful for latency distributions.

## Idempotency

A property where rerunning the same logical operation does not create unintended duplicate/corrupt results.

## Image

A built container template from which containers run.

## Inference

Using a trained model to generate a prediction.

## Lag feature

A previous time-series value used as model input.

## Lineage

Trace connecting an output to its origins.

~~~text
champion
→ model version
→ MLflow run
→ dataset fingerprint
~~~

## MAE

Mean Absolute Error: average absolute prediction error.

## MLflow run

One recorded experiment execution containing parameters, metrics, tags, and artifacts.

## Model Registry

Versioned catalog used to manage models after experiments.

## Orchestration

Coordinating workflow steps, dependencies, schedule, and execution state.

## Prometheus scrape

A request Prometheus makes to a metrics endpoint to collect current metric values.

## RMSE

Root Mean Squared Error: regression error metric that penalizes large errors more strongly.

## Rolling feature

Statistic calculated over a recent historical window.

## Serving

Exposing inference through a stable interface such as HTTP.

## Snapshot

Frozen dataset state used for one training cycle.

## Task

One unit of work in an Airflow DAG.

## Training-serving consistency

Keeping feature meaning consistent between offline training and online prediction.

## Volume

Persistent or mounted storage used by containers.

## XCom

Airflow mechanism for small task outputs/metadata. Not intended as a large DataFrame transport layer.
