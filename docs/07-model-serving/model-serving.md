# Model Serving — Model Sudah Jadi, Terus Dipakai Orang Lain Gimana?

Sampai sini kita sudah punya model yang ditrain, ditrack, dan diregister.

Kalau project berhenti di notebook, sebenarnya model masih belum terlalu useful buat system lain.

Bayangin backend engineer datang dan bilang:

> “Gue mau prediction buat zone 161 jam 18:00. Gimana caranya?”

Kalau jawaban kita:

> “Buka Python, load model, terus bikin feature lag_1h, lag_24h, rolling_mean_3h, jangan lupa category dtype, terus predict.”

Ya backend engineer-nya mungkin langsung pulang. 😭

Di sinilah model serving masuk.

---

## Serving = bikin interface yang stable

Client seharusnya nggak perlu tahu internal complexity model.

Client cukup kirim business input:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Lalu service yang handle:

~~~text
request validation
↓
history lookup
↓
online feature construction
↓
model loading
↓
prediction
↓
prediction logging
↓
response
~~~

Ini abstraction boundary.

Client tahu **what it wants**.

Service tahu **how to produce it**.

---

## Kenapa client nggak kirim lag feature?

Kita bisa saja design API:

~~~json
{
  "zone_id": 161,
  "lag_1h": 120,
  "lag_24h": 140,
  "rolling_mean_3h": 128.3,
  "rolling_mean_24h": 130.1
}
~~~

Secara teknis bisa.

Tapi siapa yang bertanggung jawab memastikan lag feature itu benar?

Sekarang setiap client harus ngerti feature engineering internal model.

Kalau feature definition berubah, semua client harus update.

Coupling-nya tinggi.

Lebih sehat kalau client kirim domain input:

~~~text
zone
target time
~~~

Serving layer yang transform ke model input.

---

## Training-serving consistency

Ini salah satu source bug paling sneaky di production ML.

Bayangin training pakai:

~~~text
rolling_mean_3h
=
mean of previous 3 complete hours
~~~

Tapi serving implementation accidentally pakai:

~~~text
current hour included
~~~

Model input semantics jadi beda.

Offline metric bagus, online behavior aneh.

Makanya training-serving consistency penting.

Workshop kita belum pakai feature store, jadi consistency dijaga lewat explicit Python implementation dan tests.

Di system besar, feature store bisa bantu centralize feature definitions.

---

## Prediction time dan leakage

Target:

~~~text
18:00
~~~

Apa data paling baru yang boleh dipakai?

~~~text
17:00
~~~

Actual 18:00 demand belum boleh masuk.

Walaupun kita pakai historical replay dan file full history technically tersedia di disk, serving function tetap enforce past-only history.

Ini penting.

MLOps pipeline yang sophisticated tetap bisa menghasilkan model cheating kalau leakage rule salah.

Tools nggak menyelamatkan bad ML logic.

---

## Model loader

Serving perlu model.

Tapi model version bisa berubah.

Kita nggak mau hard-code:

~~~text
version 3
~~~

Kita resolve:

~~~text
champion
~~~

dari MLflow Registry.

Jadi application code tidak berubah saat model promotion.

---

## Kenapa model nggak reload setiap request?

Bayangin traffic:

~~~text
100 requests/second
~~~

Kalau setiap request:

~~~text
query Registry
download model
deserialize
predict
~~~

gila juga. 😭

Model loading mahal.

Kita cache loaded model.

Registry metadata juga punya refresh interval.

Flow:

~~~text
request
↓
is cached model still current?
↓
yes → reuse

after refresh interval
↓
check champion version
↓
changed?
yes → reload
~~~

Ini balance antara freshness dan overhead.

---

## Prediction logging

Setelah prediction dibuat, kita log:

~~~text
zone_id
target_datetime
predicted_trip_count
model_version
run_id
logged_at
~~~

Kenapa?

Karena beberapa jam kemudian kita mau evaluate:

~~~text
prediction
vs
actual
~~~

Kalau prediction tidak disimpan, kita kehilangan evidence tentang apa yang model bilang saat itu.

Model monitoring butuh historical prediction records.

---

## JSONL kenapa?

Workshop pakai:

~~~text
predictions.jsonl
~~~

One JSON per line.

Kenapa simpel banget?

Karena goal-nya ngajarin lifecycle, bukan database architecture.

JSONL enak buat append.

Production system mungkin pakai:

- database,
- Kafka,
- data warehouse,
- event store.

Concept-nya sama:

> prediction event harus tersimpan dan traceable.

---

## Serving vs Deployment

Sering ketuker.

### Serving

How prediction is exposed.

~~~text
HTTP API
~~~

### Deployment

How serving application is placed in an environment.

~~~text
container
cloud platform
Kubernetes
VM
~~~

FastAPI handle serving interface.

Docker handle packaging.

CI/CD handle artifact delivery.

Different concerns.

---

## Prediction output bukan cuma angka

Response kita include model metadata.

Kenapa?

Supaya kalau ada incident:

> “Prediction aneh ini dibuat model mana?”

kita punya clue.

Traceability bukan cuma buat training.

Prediction lineage juga useful.

---

## Negative prediction

Regression model bisa mathematically output negative.

Taxi pickup count nggak mungkin negative.

Serving layer clip minimum zero.

Ini contoh domain rule.

Model output kadang perlu post-processing.

Tapi hati-hati: post-processing juga bagian behavior system dan harus terdokumentasi.

---

## Checkpoint

Coba jawab:

1. Kenapa client cuma kirim zone dan target time?
2. Apa itu training-serving consistency?
3. Kenapa champion alias lebih baik daripada hard-coded version?
4. Kenapa model di-cache?
5. Kenapa prediction harus dilog?
6. Serving dan deployment beda apa?
