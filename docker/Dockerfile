FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

# install tool minimum yang dipakai project dan bootstrap uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir uv

# pakai uid 1000 supaya file dari bind mount nggak selalu jadi milik root di host linux
RUN useradd --create-home --uid 1000 app

WORKDIR /app

# copy dependency metadata dulu supaya layer install bisa kepake ulang
COPY pyproject.toml .python-version README.md ./
COPY src ./src
COPY api ./api
COPY scripts ./scripts
COPY dvc.yaml ./
COPY .dvc ./.dvc
COPY .dvcignore ./

RUN mkdir -p /app/.dvc/cache /app/data \
    && chown -R app:app /app

USER app

# install core project tanpa dev dependency
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"


FROM base AS api

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM base AS mlflow

USER root

RUN mkdir -p /mlflow/artifacts \
    && chown -R app:app /mlflow

USER app

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "sqlite:////mlflow/mlflow.db", "--artifacts-destination", "/mlflow/artifacts", "--serve-artifacts", "--allowed-hosts", "mlflow:5000,localhost:5000,127.0.0.1:5000"]


FROM base AS airflow

# airflow dipisah ke dependency group karena jauh lebih berat dari core project
RUN uv sync --no-dev --group airflow

COPY --chown=app:app dags ./dags

USER root

RUN mkdir -p /airflow \
    && chown -R app:app /airflow

USER app

ENV AIRFLOW_HOME="/airflow"
ENV AIRFLOW__CORE__DAGS_FOLDER="/app/dags"
ENV AIRFLOW__API__HOST="0.0.0.0"

EXPOSE 8080

CMD ["python", "scripts/start_airflow.py"]
