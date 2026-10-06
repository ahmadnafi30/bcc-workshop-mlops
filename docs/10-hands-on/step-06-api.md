# Step 6 — FastAPI: Dari Champion di Registry Jadi Prediction yang Bisa Dipanggil Lewat HTTP

Sekarang kita punya champion model di MLflow Registry.

Kalau model cuma hidup di Registry, application lain belum bisa pakai.

Kita butuh serving interface.

Di step ini kita akan start FastAPI, inspect endpoint, kirim prediction, dan trace apa yang terjadi dari request sampai model response.

---

## Goal

Setelah selesai kalian harus bisa:

- explain health vs model readiness;
- inspect /model-info;
- send /predict;
- understand 422 vs 503;
- understand online feature construction;
- understand champion alias resolution;
- verify prediction logging;
- inspect /metrics;
- explain dependency injection/testing concept.

---

## 1. Pastikan MLflow jalan

Kalau local server sudah stop:

~~~bash
uv run python scripts/start_mlflow.py
~~~

Open:

~~~text
http://127.0.0.1:5000
~~~

Check champion alias.

---

# 2. Pastikan champion alias ada

Model Registry harus punya:

~~~text
champion
→ version X
~~~

Kalau belum:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

Question:

> “Kalau champion nggak ada, apakah FastAPI tahu model mana yang approved?”

No.

---

# 3. Pastikan historical demand cukup

Untuk target Jan 28 18:00, online feature provider perlu up to 168h history.

Jadi processed demand previous days harus exist.

Check:

~~~text
data/processed/demand/
~~~

Kalau history incomplete, prediction seharusnya fail clearly.

---

# 4. Start FastAPI

New terminal:

~~~bash
uv run uvicorn api.main:app --reload
~~~

Open:

~~~text
http://127.0.0.1:8000/docs
~~~

Ini Swagger UI.

---

# 5. Sebelum click, lihat endpoint list

Expected:

~~~text
GET /health
GET /model-info
POST /predict
~~~

Operational hidden endpoint:

~~~text
GET /metrics
~~~

Why hidden?

Karena /metrics bukan business API participant/client utama.

---

## 4. GET /health

Swagger atau curl:

~~~bash
curl http://127.0.0.1:8000/health
~~~

Expected:

~~~json
{"status":"ok"}
~~~

Interpretasi:

> FastAPI process alive.

Bukan:

> model definitely ready.

---

# 7. Kenapa health tidak load champion?

Kalau /health tergantung MLflow:

~~~text
MLflow down
↓
health red
~~~

Kita tidak tahu apakah API process mati atau dependency down.

Simple health signal membantu isolate layer.

Readiness probe production bisa dibuat lebih comprehensive separately.

---

# 8. Test /model-info

~~~bash
curl http://127.0.0.1:8000/model-info
~~~

Response include:

~~~text
model_name
model_version
model_alias
run_id
model_uri
~~~

Coba compare model_version dengan Registry UI.

Harus match champion alias.

---

# 9. Prediction request — sebelum send, predict internal flow

Request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Sebelum Try it out, coba sebutkan internal steps.

Expected:

~~~text
validate schema
↓
build online features from history
↓
resolve champion
↓
load/reuse model
↓
predict
↓
clip negative if needed
↓
log prediction
↓
observe Prometheus metric
↓
return response
~~~

Baru send.

---

# 10. Inspect response

Jangan cuma lihat:

~~~text
predicted_trip_count
~~~

Lihat juga:

~~~text
model_version
model_alias
run_id
model_uri
~~~

Kenapa?

Prediction lineage.

Kalau output aneh, kita tahu model mana yang produce.

---

# 11. Kenapa client tidak kirim lag feature?

Kalau request harus kirim:

~~~text
lag_1h
lag_24h
rolling_mean_3h
...
~~~

client harus ngerti feature engineering.

Bad coupling.

Dengan:

~~~text
zone_id
target_datetime
~~~

serving layer menjaga feature semantics.

---

# 12. Test invalid target time

Try:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:30:00"
}
~~~

Expected validation failure / 422.

Kenapa?

Model contract hourly.

18:30 bukan exact target hour.

---

# 13. Apa arti 422?

Roughly:

> Request structure diterima, tapi input tidak valid untuk domain/schema prediction.

Contoh:

- invalid zone;
- target minute bukan 00;
- historical feature unavailable.

Bukan server crash.

---

# 14. Simulate champion missing conceptually

Kalau champion alias tidak ada, /model-info atau /predict bisa return 503.

Apa arti 503?

> Service process alive, dependency model temporarily unavailable/not ready.

Ini beda dari 422.

---

# 15. 422 vs 503 thought exercise

### Request target 18:30

~~~text
422
~~~

Client/input problem.

### MLflow unreachable

~~~text
503
~~~

Service dependency problem.

Different action.

---

# 16. Model loader cache

First request mungkin load champion model.

Next requests reuse cache.

Kenapa?

Model load lebih mahal daripada predict.

Loader periodically refresh Registry metadata.

Jadi:

~~~text
cache fast
+
still detects champion update
~~~

Tradeoff freshness vs overhead.

---

# 17. Prediction log

Setelah successful request, inspect:

~~~text
data/monitoring/predictions.jsonl
~~~

Optional:

~~~bash
tail -n 5 data/monitoring/predictions.jsonl
~~~

Cari request kalian.

Fields:

~~~text
target_datetime
zone_id
predicted_trip_count
model_version
run_id
logged_at
~~~

Prediction event sekarang siap untuk delayed evaluation nanti.

---

# 18. Kenapa log setelah successful predict?

Kalau request invalid dan tidak ada prediction, jangan tulis fake prediction event.

Monitoring hanya evaluate actual inference yang terjadi.

Event semantics harus clear.

---

# 19. Negative output domain constraint

Regression theoretically bisa predict negative.

Serving result clip minimum zero.

Question:

> “Kenapa bukan model training saja yang guarantee?”

Model mathematical output space continuous.

Domain knows count cannot negative.

Post-processing boundary enforce valid business output.

---

# 20. Open /metrics

~~~text
http://127.0.0.1:8000/metrics
~~~

Cari:

~~~text
taxi_api_requests_total
taxi_predictions_total
taxi_model_version_info
~~~

Sekarang kalian sudah mulai melihat connection FastAPI → Prometheus.

---

# 21. Request middleware

Setiap HTTP request lewat middleware.

Concept:

~~~text
start timer
↓
endpoint
↓
response
↓
record duration
↓
increment request counter
~~~

Kalau endpoint fail pun status code metric tetap useful.

---

# 22. Test multiple requests

Send beberapa prediction.

Lihat /metrics lagi.

Counter harus naik.

Ini good prelude sebelum Step 9 monitoring.

---

# 23. Swagger vs curl

Swagger good buat learning.

curl good buat automation/simple CLI.

API contract sama.

Tool client beda.

Jangan confuse Swagger sebagai “FastAPI backend”. Swagger hanya interactive docs UI.

---

# 24. API testing architecture

Project tests override predictor dependency.

Kenapa?

Supaya test endpoint tidak butuh real:

- MLflow;
- model;
- Parquet history.

Unit/API contract test fokus satu layer.

Integration flow tetap dites lewat workshop stack.

---

# 25. Common error: /health works, /predict fails

Jangan bilang API broken.

Interpretation:

~~~text
HTTP process
✅

prediction dependency/path
❌
~~~

Check:

- champion;
- history;
- target;
- MLflow;
- model loading.

Specific diagnosis.

---

# 26. Common error: model info version unexpected

Check Registry alias.

Maybe challenger baru registered tapi champion belum moved.

Remember:

~~~text
challenger
≠
champion
~~~

API serve champion only.

---

# 27. Common error: history missing

Online feature provider membaca processed daily demand files.

Kalau lag_168h source date missing, request fail.

Correct.

Jangan silently fill zero, karena zero means actual no demand, bukan missing history.

---

# 28. Checkpoint

1. /health menjawab apa?
2. /model-info menjawab apa?
3. /predict internal flow?
4. Kenapa client tidak kirim lag features?
5. 422 vs 503?
6. Kenapa champion alias digunakan?
7. Kenapa model di-cache?
8. Prediction log dipakai kapan?
9. Negative prediction diproses bagaimana?
10. /metrics dipakai siapa?
11. Middleware mencatat apa?
12. Swagger role-nya apa?
13. /health green tapi /predict fail artinya apa?
14. Missing history kenapa tidak di-fill zero?

Kalau clear, next kita package seluruh stack pakai Docker dan Compose.
