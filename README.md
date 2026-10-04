# BCC Workshop — MLOps

End-to-end MLOps workshop project using an urban mobility / taxi demand forecasting use case.

The project will demonstrate the ML lifecycle from data ingestion and orchestration to experiment tracking, model serving, containerization, CI/CD, monitoring, and retraining.

## Planned Stack

- Python
- Airflow
- DVC
- MLflow
- FastAPI
- Docker / Docker Compose
- GitHub Actions
- Prometheus
- Grafana

## Project Status

🚧 Work in progress — the repository structure is being prepared before the workshop implementation is added.

## Documentation

Workshop materials and hands-on guides live under `docs/`.

## High-level Flow

```text
Data
  ↓
Airflow
  ↓
DVC snapshot
  ↓
Training
  ↓
MLflow
  ↓
FastAPI
  ↓
Docker
  ↓
GitHub Actions
  ↓
Monitoring
  ↓
Retraining
```
