# FastAPI — Membungkus Model Jadi HTTP Service yang Enak Dipakai

FastAPI bukan “ML tool”.

Dan justru itu point-nya.

Machine Learning production banyak banget bersentuhan dengan normal software engineering.

Kita butuh interface yang:

- typed,
- validated,
- documented,
- testable,
- gampang dipakai client.

FastAPI cocok banget untuk itu.

---

## Folder separation

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

Kenapa nggak semuanya di api/main.py?

Karena HTTP concern dan ML domain concern beda.

Kalau besok kita ganti FastAPI dengan framework lain, model logic seharusnya nggak perlu ditulis ulang total.

---

## schemas.py — contract

Pydantic schema define bentuk request/response.

Contoh request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Validation bisa catch:

~~~text
zone_id <= 0
target minute != 00
timezone format unsupported
~~~

Lebih baik reject request invalid di boundary daripada biarkan error muncul jauh di model layer.

---

## main.py — HTTP layer

Responsibility:

- endpoint,
- middleware,
- exception → HTTP status,
- response schema.

Bukan tempat:

- train model,
- 200 lines Pandas,
- model registry implementation.

HTTP layer harus relatively thin.

---

## dependencies.py — dependency wiring

Kita create predictor lewat dependency.

Benefit besar saat testing.

Production:

~~~text
real predictor
→ MLflow
→ real model
~~~

Test:

~~~text
fake predictor
→ deterministic result
~~~

Jadi API contract bisa dites tanpa menyalakan seluruh MLOps stack.

---

# GET /health

~~~http
GET /health
~~~

Response:

~~~json
{
  "status": "ok"
}
~~~

Kenapa endpoint ini **nggak sekalian check MLflow, data history, champion, Prometheus, dan segalanya?**

Karena kita ingin signal yang specific.

Kalau /health fail karena MLflow down, kita nggak tahu:

~~~text
FastAPI process mati?
atau
dependency MLflow yang mati?
~~~

Health endpoint project ini menjawab narrow question:

> “FastAPI process bisa respond nggak?”

Dependency readiness bisa dilihat dari endpoint lain.

---

# GET /model-info

Endpoint ini answer:

> “Model apa yang sekarang dipakai?”

Response include:

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

Interpretation:

> API alive, tapi dependency model belum ready.

Ini lebih informative daripada generic 500.

---

# POST /predict

Flow:

~~~text
request
↓
Pydantic validation
↓
feature provider
↓
model loader
↓
predictor
↓
prediction logger
↓
metric observer
↓
response
~~~

Perhatikan layering.

Endpoint nggak bikin rolling feature sendiri.

Dia delegate ke serving logic.

---

## Kenapa 422?

422 berarti request bisa dipahami secara struktur, tapi tidak valid untuk semantic use case.

Contoh:

~~~text
target_datetime = 18:30
~~~

Model kita hourly.

Atau history 168 jam belum lengkap.

Client request tidak bisa dipenuhi dengan contract current model.

---

## Kenapa 503?

503 berarti service secara umum hidup, tapi dependency sementara unavailable.

Contoh:

~~~text
champion alias belum ada
MLflow registry unavailable
~~~

Ini berbeda dari validation error.

---

## Middleware

HTTP middleware wrap setiap request.

Conceptual:

~~~text
request arrives
↓
start timer
↓
endpoint runs
↓
response generated
↓
stop timer
↓
record latency + status
~~~

Prometheus metric update terjadi di sini.

Kenapa middleware?

Karena kita nggak mau copy metric timing code ke setiap endpoint.

Cross-cutting concern cocok di middleware.

---

## /metrics

Prometheus scrape:

~~~http
GET /metrics
~~~

Endpoint ini operational, bukan business API.

Makanya hidden dari main Swagger schema.

Client taxi prediction nggak perlu tahu metric endpoint.

---

## Swagger UI

Start:

~~~bash
uv run uvicorn api.main:app --reload
~~~

Open:

~~~text
http://127.0.0.1:8000/docs
~~~

Swagger useful banget buat workshop karena peserta bisa:

- lihat endpoint,
- lihat schema,
- coba request,
- lihat status code,
- lihat response.

Tanpa harus hafal curl dulu.

---

## Testing layers

Jangan semua test dijadikan full integration test.

### Unit test

Test function kecil.

### API contract test

FastAPI + fake predictor.

Focus request/response/status.

### Integration

Real MLflow + model + history + API.

Lebih berat.

Kenapa dipisah?

Kalau every unit test harus boot MLflow dan download model, test jadi lambat dan flaky.

---

## Path cardinality

Prometheus metric label bisa bahaya.

Kalau path arbitrary dipakai raw:

~~~text
/user/1
/user/2
/user/3
...
~~~

bisa create banyak time series.

Project normalize path yang dikenal.

Unknown path jadi:

~~~text
other
~~~

Ini contoh operational design detail yang kecil tapi important.

---

## Common debugging

### /health 200, /predict 503

API sehat.

Model dependency problem.

### /predict 422

Request/history problem.

### connection refused

API process / port problem.

### model version unexpected

Check champion alias.

---

## Mini challenge

Kalau besok mau tambah endpoint batch prediction, apakah semua model loading logic di-copy ke endpoint baru?

No.

Pattern yang lebih sehat:

~~~text
new schema
↓
reuse predictor/service logic
↓
thin endpoint wrapper
~~~

Framework layer tipis, domain logic reusable.

Pattern ini mirip Airflow DAG tipis yang call src functions.
