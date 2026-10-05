# Step 6 — FastAPI: Making Our Champion Model Usable

Sampai sini kita punya model di Registry.

Sekarang kita pindah perspective.

Bukan lagi:

> “Gimana Data Scientist train model?”

Tapi:

> “Gimana application lain pakai model ini?”

Ini transition penting dari ML experiment ke ML service.

---

# Target step

Setelah selesai:

- MLflow champion tersedia,
- FastAPI running,
- kalian bisa hit /health,
- kalian bisa inspect /model-info,
- kalian bisa POST /predict,
- kalian ngerti apa yang terjadi di belakang satu request.

---

# 1. Pastikan MLflow hidup

Kalau Airflow masih jalan, itu okay.

Start local MLflow kalau belum:

~~~bash
uv run python scripts/start_mlflow.py
~~~

Open:

~~~text
http://127.0.0.1:5000
~~~

---

# 2. Check champion

Open Model Registry.

Cari:

~~~text
taxi-demand-forecasting-model
~~~

Pastikan ada alias:

~~~text
champion
~~~

Kalau belum:

~~~bash
uv run python scripts/promote_model.py   --version <VERSION>
~~~

Kenapa ini wajib?

Karena API sengaja tidak hard-code version.

Tanpa champion, API tidak tahu model mana yang approved.

---

# 3. Pastikan history cukup

Prediction target Jan 28 18:00 butuh history hingga 168h ke belakang.

Kalau kalian sudah replay Jan 27 dan Jan 28 via Airflow, harusnya history ada.

Kalau belum, prediction bisa return 422.

Ini bukan API bug.

Itu data readiness problem.

---

# 4. Start FastAPI

Open terminal baru:

~~~bash
uv run uvicorn api.main:app --reload
~~~

Output biasanya menunjukkan:

~~~text
Uvicorn running on http://127.0.0.1:8000
~~~

---

# 5. Open Swagger

~~~text
http://127.0.0.1:8000/docs
~~~

Ini salah satu bagian seru buat demo karena peserta bisa interact langsung.

Kalian akan lihat endpoint utama.

---

# 6. Test /health

Klik:

~~~text
GET /health
~~~

Execute.

Expected:

~~~json
{
  "status": "ok"
}
~~~

Sekarang pertanyaan penting:

> Apakah berarti model champion pasti ready?

No.

Health endpoint hanya verify API process.

---

# 7. Test /model-info

~~~text
GET /model-info
~~~

Execute.

Expected ada:

~~~text
model_name
model_version
model_alias
run_id
model_uri
~~~

Coba compare model_version ini dengan MLflow Registry UI.

Harus match champion.

---

# 8. Test /predict

Request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Execute.

Response roughly:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00",
  "predicted_trip_count": 147.8,
  "model_name": "...",
  "model_version": "1",
  "model_alias": "champion",
  "run_id": "..."
}
~~~

Actual prediction value bisa berbeda. Jangan terpaku ke contoh angka.

---

# 9. Pause: what just happened?

Client cuma kasih:

~~~text
zone_id
target_datetime
~~~

Tapi model butuh 12 features.

Berarti siapa yang build?

Serving backend.

Flow:

~~~text
HTTP request
↓
schema validation
↓
history lookup
↓
online feature engineering
↓
champion model loading
↓
prediction
↓
prediction logging
↓
response
~~~

Satu endpoint sebenarnya menggabungkan banyak layer.

---

# 10. Coba request invalid time

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:30:00"
}
~~~

Apa yang terjadi?

Harus rejected.

Kenapa?

Karena model contract hourly.

Ini good API design:

> Reject invalid semantic input early.

---

# 11. Coba bayangin champion berubah

Saat API jalan, promotion bisa pindah:

~~~text
champion v1
→
champion v2
~~~

Serving loader punya refresh interval.

Setelah re-check, model baru bisa diload tanpa edit API source.

Itulah benefit alias.

---

# 12. Inspect prediction log

Setelah successful prediction, check:

~~~text
data/monitoring/predictions.jsonl
~~~

Kalian akan lihat one JSON object per line.

Kenapa prediction disimpan?

Karena nanti ground truth datang setelah target hour.

---

# Mini challenge

Pertanyaan:

> Kenapa response include model_version dan run_id?

Jawaban:

> Biar prediction traceable ke model lineage.

Kalau nanti ada complaint:

> “Prediction jam 18:00 kok aneh?”

kita bisa cari model mana yang menghasilkan.

---

# Common issues

## /health okay, /model-info 503

FastAPI alive.

MLflow/champion unavailable.

## /predict 422

Check:

- target time exact hour?
- 168h history complete?
- processed date available?

## connection refused

Uvicorn belum running atau wrong port.

---

# Checkpoint

Kalian harus bisa answer:

> Serving itu apa bedanya dengan training?

Training menghasilkan model.

Serving membuat model usable oleh application.

Next kita package semua service pakai Docker.
