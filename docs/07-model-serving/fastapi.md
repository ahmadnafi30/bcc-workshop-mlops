# FastAPI

FastAPI jadi HTTP layer untuk model serving kita.

Core logic-nya tetap ada di:

```text
src/serving/
├── feature_provider.py
├── model_loader.py
└── predictor.py
```

Sedangkan:

```text
api/
├── schemas.py
├── dependencies.py
└── main.py
```

fokus ke request, response, dependency injection, dan HTTP error.

## Sebelum start API

Pastikan project sudah siap:

```bash
uv sync
```

MLflow server juga harus hidup:

```bash
uv run mlflow server
```

dan registry harus punya alias:

```text
champion
```

Kalau belum, promote model version yang sudah direview:

```bash
uv run python scripts/promote_model.py --version <VERSION>
```

## Start API

```bash
uv run uvicorn api.main:app --reload
```

Default address:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## GET /health

```bash
curl http://127.0.0.1:8000/health
```

Response:

```json
{
  "status": "ok"
}
```

Endpoint ini cuma ngecek API process hidup. Dia sengaja nggak bergantung ke MLflow.

## GET /model-info

```bash
curl http://127.0.0.1:8000/model-info
```

Endpoint ini ngecek model yang sekarang ditunjuk alias serving.

Kalau champion belum ada, response-nya 503.

## POST /predict

Contoh:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": 161,
    "target_datetime": "2025-01-28T18:00:00"
  }'
```

Flow internal:

```text
request validation
       ↓
load 168h history
       ↓
build online features
       ↓
resolve champion alias
       ↓
load / refresh model
       ↓
predict
       ↓
response
```

## Kenapa ada /model-info?

Ini useful buat observability dan debugging.

Kita bisa jawab:

```text
API sekarang sebenarnya pakai model version berapa?
run MLflow mana?
alias apa?
```

Nanti endpoint ini juga berguna saat kita masuk Docker dan monitoring.

## Error yang sengaja dibedakan

**422**

request valid secara JSON, tapi prediction nggak bisa dibuat. Misalnya history demand belum lengkap.

**503**

API hidup, tapi champion model dari MLflow Registry belum ready.

Ini lebih berguna daripada semua error dibalikin jadi generic 500.

## Tests

API test pakai FastAPI `TestClient` dan dependency override.

Jadi unit test nggak perlu benar-benar nyalain MLflow server:

```bash
uv run pytest tests/test_api.py tests/test_predictor.py tests/test_serving_features.py
```

Model dan registry diganti fake object khusus test. Ini bikin test cepat dan deterministic.
