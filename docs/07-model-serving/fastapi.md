# FastAPI — Membungkus Model Jadi HTTP Service yang Beneran Bisa Dipakai

FastAPI bukan Machine Learning tool.

Dan justru itu menarik.

Begitu model mau dipakai user atau system lain, kita masuk dunia normal software engineering: API contract, validation, error handling, dependency injection, testing, dan observability.

MLOps bukan dunia terpisah dari software engineering. MLOps justru banyak memakai software engineering practice supaya model usable dan maintainable.

---

## Kenapa FastAPI?

Kita butuh service yang:

- bisa expose HTTP endpoint;
- punya typed request/response;
- gampang validasi input;
- punya auto-generated docs;
- gampang dites;
- cocok dengan Python ecosystem.

FastAPI fit banget buat workshop.

Tapi jangan terlalu attach ke brand tool-nya. Kalau besok pakai framework lain, core serving concept tetap sama.

---

## Struktur project serving

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

Ini intentional separation.

Kalau semua ditaruh di main.py, file itu cepat berubah jadi monster.

---

## schemas.py — define contract

Pydantic schema bilang request valid bentuknya apa.

Contoh:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Kita bisa enforce rule seperti:

~~~text
zone_id harus positive
target minute harus 00
target second harus 00
~~~

Kenapa validation di boundary penting?

Karena lebih baik reject:

> “Target harus exact hour.”

daripada request invalid masuk jauh ke feature provider lalu error aneh beberapa layer kemudian.

---

## main.py — HTTP concern

main.py bertanggung jawab untuk:

- endpoint route;
- response schema;
- middleware;
- mapping exception ke HTTP status;
- orchestration request.

main.py bukan tempat training model atau 300 lines Pandas feature engineering.

Kita pengen HTTP layer tipis.

Pattern ini mirip Airflow:

~~~text
DAG tipis
→ call domain logic

FastAPI endpoint tipis
→ call serving logic
~~~

---

## dependencies.py — wiring object yang dibutuhkan endpoint

Predictor dibuat lewat FastAPI dependency.

Benefit besar saat testing.

Production:

~~~text
endpoint
→ real predictor
→ MLflow
→ champion model
~~~

Test:

~~~text
endpoint
→ fake predictor
→ deterministic response
~~~

Jadi API contract bisa dites tanpa menyalakan seluruh MLOps stack.

---

## GET /health

~~~http
GET /health
~~~

Response:

~~~json
{
  "status": "ok"
}
~~~

Kelihatannya terlalu simple?

Memang.

Pertanyaannya narrow:

> “FastAPI process hidup dan bisa response nggak?”

Kita sengaja tidak membuat health endpoint tergantung semua service.

Kalau /health fail hanya karena MLflow down, kita sulit distinguish process API mati vs dependency down.

Signal yang specific lebih useful.

---

## GET /model-info

Endpoint ini jawab:

> “Model mana yang sekarang ditunjuk serving alias?”

Response punya metadata seperti:

~~~text
model_name
model_version
model_alias
run_id
model_uri
~~~

Kalau champion belum ada:

~~~text
503 Service Unavailable
~~~

Interpretasinya:

> API process alive, tapi dependency model belum ready.

---

## POST /predict

Flow actual:

~~~text
HTTP request
    ↓
Pydantic validation
    ↓
FastAPI dependency
    ↓
TaxiDemandPredictor
    ↓
online feature provider
    ↓
Registry model loader
    ↓
model.predict
    ↓
prediction logger
    ↓
Prometheus observation
    ↓
typed response
~~~

Endpoint sendiri tidak implement semua itu.

Dia delegate.

---

## Kenapa typed response?

Typed response membantu:

- documentation;
- validation;
- editor support;
- contract consistency.

Client tahu bentuk output yang bisa diharapkan.

---

## HTTP status code — jangan 500 semua

### 200

Request berhasil.

### 422

Request valid sebagai HTTP/JSON, tapi tidak valid secara semantic untuk prediction.

Contoh target 18:30 padahal model hourly, atau required history tidak lengkap.

### 503

Service process hidup, tapi dependency penting unavailable.

Contoh champion alias belum ada atau MLflow Registry unreachable.

Distinction ini membantu debugging:

~~~text
422
→ client/input/data issue

503
→ dependency readiness issue
~~~

---

## Middleware

Kita ingin ukur latency dan request count.

Kalau implement manual di tiap endpoint, duplication.

Middleware wrap request lifecycle:

~~~text
request masuk
↓
start timer
↓
endpoint execute
↓
response keluar
↓
stop timer
↓
record metric
~~~

Cross-cutting concern seperti metrics cocok di middleware.

---

## /metrics

Prometheus scrape:

~~~text
GET /metrics
~~~

Endpoint ini operational, bukan business API.

Makanya hidden dari main Swagger interface.

User taxi forecast nggak perlu interact dengan Prometheus contract.

---

## Path cardinality

Prometheus label bisa berbahaya kalau arbitrary URL dipakai raw.

Contoh:

~~~text
/users/1
/users/2
/users/3
...
~~~

Setiap unique label combination bisa menjadi time series baru.

Project normalize path yang dikenal.

Unknown jadi:

~~~text
other
~~~

Ini detail kecil tapi bagus banget buat menunjukkan observability perlu design.

---

### Middleware dalam alur request

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

### Cek endpoint /metrics dari sisi client

Prometheus scrape:

~~~http
GET /metrics
~~~

Endpoint ini operational, bukan business API.

Makanya hidden dari main Swagger schema.

Client taxi prediction nggak perlu tahu metric endpoint.

---

### Swagger UI

Start:

~~~bash
uv run uvicorn api.main:app --reload
~~~

Open:

~~~text
http://127.0.0.1:8000/docs
~~~

Di Swagger participant bisa lihat endpoint, schema, coba request, lihat status code, dan response tanpa hafal curl.

---

## Champion harus ada sebelum predict

Urutannya:

~~~text
start MLflow
↓
register model
↓
promote champion
↓
start FastAPI
↓
predict
~~~

Kalau champion belum ada, API tidak tahu model mana yang approved.

503 di sini bukan bug. Contract bekerja sesuai design.

---

## Testing strategy

Jangan semua test dijadikan full integration test.

### Unit test

Test function kecil.

### API contract test

FastAPI dengan fake predictor.

Focus request, response, status.

### Integration demo

Real MLflow + real model + real data + FastAPI.

Focus seluruh stack nyambung.

Kalau setiap test boot MLflow dan load dataset, test jadi lambat dan flaky.

---

## Mini challenge

Suppose kita mau tambah batch prediction endpoint.

Apakah semua model loading dan feature logic di-copy?

No.

Pattern sehat:

~~~text
new schema
↓
reuse predictor/service logic
↓
thin HTTP wrapper
~~~

Ini recurring theme project kita: framework-specific layer tipis, reusable logic di src.

---

## Checkpoint

1. Kenapa schemas dipisah?
2. Kenapa /health tidak check semua dependency?
3. 422 dan 503 beda makna apa?
4. Middleware useful buat apa?
5. Kenapa /metrics bukan business endpoint?
6. Apa risiko high-cardinality label?
7. Kenapa API test bisa pakai fake predictor?
8. Kalau tambah endpoint baru, logic mana yang sebaiknya reuse?
