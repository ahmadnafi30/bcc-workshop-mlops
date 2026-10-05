# FastAPI — Building the Prediction Interface

## Kenapa FastAPI?

Kita butuh HTTP interface yang:

- gampang dibuat,
- punya request validation,
- punya auto docs,
- gampang dites,
- cocok dengan Python ML stack.

FastAPI fit banget.

Tapi yang penting bukan brand tool-nya.

Yang penting concept:

> Model inference dibungkus dalam stable service interface.

---

# Folder separation

~~~text
api/
├── main.py
├── schemas.py
└── dependencies.py

src/serving/
├── feature_provider.py
├── model_loader.py
└── predictor.py
~~~

Kenapa dipisah?

Karena HTTP concern dan ML serving concern beda.

---

# api/main.py

Responsibility:

- define endpoints,
- HTTP status handling,
- middleware,
- response objects.

Dia bukan tempat train model.

Dia bukan tempat implement rolling feature 200 lines.

---

# schemas.py

Pydantic model define request/response contract.

Contoh request:

~~~text
zone_id
target_datetime
~~~

Validation bisa ensure:

- zone_id positive,
- target time at exact hour,
- no timezone ambiguity untuk workshop mode.

---

# dependencies.py

Build reusable predictor dependency.

FastAPI dependency injection memudahkan testing.

Di test, real predictor bisa diganti fake.

Jadi API contract bisa dites tanpa MLflow server real.

---

# GET /health

Response:

~~~json
{
  "status": "ok"
}
~~~

Apa arti health?

> FastAPI process alive dan bisa respond.

Apa yang **tidak** dijamin?

- champion exists,
- MLflow healthy,
- history data complete.

Kenapa health tidak check everything?

Kalau health endpoint depends on semua dependency, sulit distinguish:

~~~text
API process down
vs
MLflow dependency down
~~~

Separation health signal bisa lebih informative.

---

# GET /model-info

Endpoint ini query Registry metadata.

Response roughly:

~~~text
model_name
model_version
model_alias
run_id
model_uri
~~~

Kalau champion missing:

~~~text
503 Service Unavailable
~~~

Meaning:

> API alive, model dependency not ready.

---

# POST /predict

Request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Flow:

~~~text
Pydantic validation
↓
feature provider
↓
registry loader
↓
model predict
↓
prediction logger
↓
response
~~~

---

# Why 422?

Contoh:

~~~text
target_datetime = 18:30
~~~

Model kita hourly.

Request valid JSON, tapi semantically invalid buat prediction contract.

FastAPI/Pydantic return 422.

History incomplete juga mapped ke 422 in project.

---

# Why 503?

Model dependency unavailable.

Contoh:

~~~text
champion alias missing
~~~

API code itself healthy.

Dependency not ready.

---

# Swagger UI

Start:

~~~bash
uv run uvicorn api.main:app --reload
~~~

Open:

~~~text
http://127.0.0.1:8000/docs
~~~

Swagger membantu newbie karena:

- endpoint list visible,
- schema visible,
- request bisa dicoba langsung,
- response code visible.

Presenter bisa demo tanpa curl.

---

# Start MLflow first

Sebelum model-info/predict:

~~~bash
uv run python scripts/start_mlflow.py
~~~

Pastikan Registry punya champion.

Kalau nggak, API nggak punya model yang harus diserve.

---

# Middleware metrics

API punya HTTP middleware yang record:

- request count,
- latency,
- status.

Setiap request melewati middleware.

Flow:

~~~text
request starts
↓
timer starts
↓
endpoint executes
↓
response
↓
timer stops
↓
Prometheus metric updated
~~~

---

# /metrics

Prometheus scrape:

~~~text
GET /metrics
~~~

Endpoint return exposition format.

Hidden dari main Swagger schema karena bukan business API.

Dia operational endpoint.

---

# Path label normalization

Prometheus label bisa explode cardinality kalau arbitrary URL path dipakai.

Project normalize known paths.

Unknown jadi:

~~~text
other
~~~

Kenapa?

Kita nggak mau millions unique metric series karena dynamic URL.

---

# Testing API tanpa real MLflow

Test use dependency override.

FakePredictor return deterministic data.

Kenapa useful?

Karena unit test API harus test:

- request validation,
- response structure,
- HTTP code.

Bukan startup full MLflow.

Integration test bisa separate.

---

# Testing layers

Mental model:

~~~text
unit test
→ function behavior

API contract test
→ HTTP behavior with fake dependency

integration
→ real MLflow + data + model + API
~~~

Jangan paksa setiap test jadi full integration test.

Nanti lambat dan flaky.

---

# Common debugging

## /health works, /predict 503

API healthy.

MLflow/champion problem.

## /predict 422

Request/history problem.

## connection refused

API process not running / wrong port.

## model-info version unexpected

Check champion alias in MLflow.

---

# Takeaway

FastAPI bukan “ML tool”.

Dia application interface.

Itu justru bagus.

MLOps banyak menggunakan normal software engineering practice untuk membuat ML usable.


---

# Implementation Deep Dive — Endpoint Kita

Health endpoint actual-nya sangat kecil:

~~~python
@app.get(
    "/health",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
~~~

Endpoint kecil tetap useful karena health probe harus cheap dan predictable.

## Prediction endpoint

Simplified:

~~~python
@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(
    request: PredictionRequest,
    predictor: TaxiDemandPredictor = Depends(
        get_predictor
    ),
) -> PredictionResponse:

    result = predictor.predict(
        zone_id=request.zone_id,
        target_datetime=request.target_datetime,
    )

    observe_prediction(result)

    return PredictionResponse(**result)
~~~

Baca flow:

~~~text
typed request
↓
dependency-injected predictor
↓
domain prediction
↓
metric observation
↓
typed response
~~~

HTTP layer tetap tipis.

Actual history/model logic ada di src/serving.

## Kalau bikin endpoint baru

Misalnya batch prediction.

Jangan duplicate semua model loading ke endpoint.

Design:

~~~text
schema
↓
reusable serving function
↓
HTTP wrapper
~~~

Framework layer tipis, domain logic reusable. Pattern ini sama seperti DAG tipis di Airflow.
