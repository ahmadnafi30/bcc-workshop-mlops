# Step 6 — FastAPI: Sekarang Model Kita Harus Bisa Dipakai System Lain

Sampai sini model sudah punya champion di Registry.

Tapi kalau mau dipakai application lain, kita butuh stable interface.

Sekarang kita bikin model “keluar dari notebook” dan bisa di-request lewat HTTP.

---

## Goal

Setelah step ini:

- MLflow champion tersedia,
- FastAPI hidup,
- health endpoint works,
- model-info menunjukkan champion,
- prediction request berhasil,
- kalian ngerti behind-the-scenes online feature construction.

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

## 2. Pertanyaan sebelum start API

Kalau champion alias belum ada, menurut kalian /health harus fail nggak?

Think.

Answer project kita:

~~~text
/health
→ tetap bisa 200

/model-info
→ 503
~~~

Kenapa?

Karena FastAPI process hidup, tapi model dependency belum ready.

Signal dipisah.

---

## 3. Start API

~~~bash
uv run uvicorn api.main:app --reload
~~~

Open:

~~~text
http://127.0.0.1:8000/docs
~~~

Swagger UI akan jadi playground kita.

---

## 4. GET /health

Click endpoint.

Try it out.

Expected:

~~~json
{
  "status": "ok"
}
~~~

Ini health process, bukan full system certification.

---

## 5. GET /model-info

Try.

Expected fields:

~~~text
model_name
model_version
model_alias
run_id
model_uri
~~~

Pause.

Tanya ke audience:

> “Kenapa run_id ikut dikembalikan? User butuh?”

End user mungkin nggak.

Tapi operational/debugging lineage useful.

Kalau prediction aneh, kita bisa trace model source run.

---

## 6. POST /predict

Request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Before click Execute, coba tebak:

> “Apakah API langsung pass dua field ini ke model?”

No.

Model butuh lags/rolling.

Service harus build feature.

---

## 7. Behind the scenes

~~~text
zone + target time
↓
load historical demand
↓
verify 168h history
↓
build calendar feature
↓
build lag
↓
build rolling
↓
load champion
↓
predict
↓
log prediction
↓
record metric
↓
response
~~~

Ini jauh lebih banyak daripada model.predict.

Serving layer adalah real application logic.

---

## 8. Try invalid time

Request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:30:00"
}
~~~

Expected 422.

Kenapa?

Model granularity hourly.

18:30 nggak match contract.

Validation fail early.

---

## 9. Check prediction log

Setelah successful prediction:

~~~text
data/monitoring/predictions.jsonl
~~~

Open last line.

Cari:

- zone,
- target,
- prediction,
- version,
- run ID.

Ini akan dipakai Step 9.

---

## 10. Try /metrics

Open:

~~~text
http://127.0.0.1:8000/metrics
~~~

Raw text kelihatan messy.

Itu normal.

Prometheus nanti baca.

Coba search:

~~~text
taxi_api_requests_total
~~~

Kalian sudah mulai lihat operational telemetry.

---

## Mini challenge

Kalau model champion berubah dari v1 ke v2, apakah API source code perlu edit?

No.

Loader resolve champion.

Kalau API restart, dia load current champion.

Saat running, loader juga periodically refresh metadata.

---

## Checkpoint

1. Kenapa health tidak check semua dependency?
2. Model-info useful buat apa?
3. Kenapa client tidak kirim lag features?
4. 422 vs 503 bedanya?
5. Prediction log dipakai untuk apa?
6. Kenapa metrics endpoint raw text?
