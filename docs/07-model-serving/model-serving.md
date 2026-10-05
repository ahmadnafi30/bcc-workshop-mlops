# Model Serving — How Does Another Application Use Our Model?

## Sampai sini model kita sudah ada

Kita sudah punya:

- training snapshot,
- model training,
- MLflow run,
- registered model,
- champion alias.

Terus sekarang ada backend developer datang:

> “Oke modelnya bagus. Gimana aplikasi saya pakainya?”

Kalau jawaban kita:

> “Import saja Python file ini, load joblib, terus build lag features sendiri ya.”

itu kurang ideal.

Kenapa?

Karena external client jadi harus ngerti internal ML implementation.

Kita butuh interface yang lebih stable.

Masuk **model serving**.

---

# Serving itu apa?

Serving berarti membuat model bisa digunakan oleh system lain melalui interface tertentu.

Interface kita:

~~~text
HTTP API
~~~

dengan FastAPI.

Jadi client tidak berinteraksi langsung dengan sklearn object.

Client cukup kirim business input.

---

# Request kita sengaja simple

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Client tidak perlu kirim:

~~~text
lag_1h
lag_2h
lag_24h
lag_168h
rolling_mean_3h
...
~~~

Kenapa?

Karena itu model implementation detail.

Kalau nanti feature berubah, kita nggak ingin semua client harus ikut update knowledge internal.

---

# Analogi waiter

Model = kitchen.

Client = customer.

Customer cukup bilang:

> “Saya pesan menu A.”

Customer nggak perlu masuk kitchen dan bilang:

> “Tolong potong bawang ukuran 3 mm, masak 7 menit, pakai 2 gram garam.”

Serving layer = waiter.

Dia menerima simple request lalu translate ke internal process.

---

# Internal serving flow

Saat request masuk:

~~~text
zone_id + target_datetime
        ↓
validate request
        ↓
load historical demand
        ↓
build online features
        ↓
resolve champion model
        ↓
predict
        ↓
clip negative value
        ↓
log prediction
        ↓
return response
~~~

Ada banyak work di balik satu endpoint.

---

# Historical demand lookup

Model butuh lag sampai:

~~~text
168 hours
~~~

Jadi serving layer baca historical demand sebelum target.

Untuk target:

~~~text
Jan 28 18:00
~~~

history window roughly:

~~~text
Jan 21 18:00
through
Jan 28 17:00
~~~

Target 18:00 itself tidak boleh dibaca.

---

# History completeness

Kalau history missing, API fail.

Kenapa tidak fill sembarangan?

Karena silent feature corruption lebih dangerous.

Lebih baik:

~~~text
HTTP 422
history incomplete
~~~

daripada return prediction yang kelihatan valid tapi feature salah.

---

# Online feature construction

Serving feature provider build satu row:

~~~text
zone_id
hour
day_of_week
is_weekend
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Schema harus match training.

---

# Training-serving skew

Ini concept penting.

Suppose training:

~~~text
lag_24h
= exact demand 24 hours earlier
~~~

Tapi serving bug:

~~~text
lag_24h
= 23 hours earlier
~~~

Model technically tetap menerima number.

No crash.

Tapi semantics berubah.

Itulah training-serving skew.

Offline metric bisa bagus, online prediction jelek.

Makanya feature consistency perlu dijaga dan dites.

---

# Model loading

API tidak hard-code:

~~~text
version 3
~~~

Dia resolve:

~~~text
champion
~~~

dari MLflow Registry.

Benefit:

~~~text
model promotion
does not require
application source code change
~~~

---

# Registry metadata cache

Kalau setiap prediction query Registry:

~~~text
which version is champion?
~~~

itu unnecessary overhead.

Loader cache metadata untuk short interval.

Saat interval expire, check alias lagi.

Kalau alias pindah:

~~~text
champion v3
→
champion v5
~~~

loader detect version change lalu reload model.

---

# Prediction output

Response bukan cuma predicted value.

Kita include lineage:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00",
  "predicted_trip_count": 147.8,
  "model_name": "taxi-demand-forecasting-model",
  "model_version": "3",
  "model_alias": "champion",
  "run_id": "..."
}
~~~

Kenapa?

Kalau ada suspicious prediction, kita bisa trace:

> “Prediction ini dibuat model version berapa?”

Observability begins from good metadata.

---

# Prediction logging

Setiap successful prediction kita append ke:

~~~text
data/monitoring/predictions.jsonl
~~~

Kenapa harus log?

Karena actual ground truth baru tersedia later.

Tanpa log prediction historical:

~~~text
actual comes later
but
we forgot what we predicted
~~~

nggak bisa calculate performance.

---

# JSONL

JSON Lines:

~~~text
one JSON object
per line
~~~

Simple untuk append-only workshop logging.

Production mungkin pakai:

- database,
- Kafka,
- warehouse,
- object storage.

Tapi concept same:

> Prediction needs durable record for future evaluation.

---

# Negative prediction

Regression mathematically bisa output negative.

Taxi pickups tidak bisa negative.

Serving layer enforce domain constraint:

~~~text
max(0, prediction)
~~~

Ini example post-processing.

---

# Serving vs deployment

Jangan campur.

## Serving

~~~text
How is prediction exposed?
~~~

FastAPI.

## Deployment

~~~text
Where/how is serving application running?
~~~

Docker/container platform.

FastAPI serving bisa jalan tanpa Docker.

Docker package serving app.

---

# Checkpoint

Kalau kalian bisa explain:

> “Kenapa request API nggak minta lag features?”

jawaban ideal:

> Karena external contract sebaiknya business-oriented, sementara feature engineering adalah internal serving responsibility.

Itu principle yang transferable ke banyak ML systems.
