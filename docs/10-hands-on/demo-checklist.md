# Presenter Demo Checklist

Presenters:

- **Ahmad Nafi Mubarok**
- **Fatoni Murfid Syafii**

## Before workshop day

### Repository

- main and develop aligned;
- CI on main green;
- docs strict build green;
- no generated data or secret committed.

### Environment

~~~bash
uv sync --group docs
uv sync --group airflow
uv run pytest
~~~

### Data

Pre-download TLC data if internet may be unreliable.

Prepare at least the historical dates required by the live demo.

### MLflow backup state

Keep one known-good experiment, registered model, and champion ready in .mlflow.

You can still demonstrate the steps live; the backup prevents network problems from stopping the workshop.

### Docker

If time is limited:

~~~bash
docker compose build
~~~

before participants arrive.

### Ports

Check 3000, 5000, 8000, 8080, and 9090.

## Teaching sequence

1. start from the model-only problem;
2. show trip data → hourly demand → features;
3. compare baseline and ML model;
4. introduce DVC and MLflow;
5. draw workflow before showing Airflow;
6. use Swagger for serving;
7. explain Compose networking;
8. open a real GitHub Actions run;
9. generate API traffic and show Grafana;
10. finish with healthy vs degraded retraining paths.

## Useful browser tabs

- workshop docs,
- GitHub Actions,
- MLflow,
- Airflow,
- FastAPI Swagger,
- Prometheus Targets,
- Grafana.

## If live demo fails

1. name the failed layer;
2. show the expected dependency;
3. use prepared state if needed;
4. continue the lifecycle explanation.

The workshop is about understanding MLOps, not proving that venue Wi-Fi is reliable.

## Final participant question

Ask:

> If the API is fast but model accuracy is getting worse, which monitoring path tells us?

A good answer mentions prediction logs, delayed ground truth, and model performance evaluation.
