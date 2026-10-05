# Model Serving — Model Sudah Jadi, Terus Orang Lain Pakainya Gimana?

Nah sekarang posisi kita sudah lumayan jauh.

Kita sudah punya data, feature engineering, baseline, model utama, experiment tracking, bahkan Model Registry. Kalau konteksnya cuma research atau tugas kuliah, mungkin sampai sini saja sudah cukup. Tapi kalau model ini mau dipakai application lain, kita punya satu problem baru:

> “Gimana caranya system lain minta prediction tanpa harus ngerti semua detail ML di belakangnya?”

Ini point masuk ke **model serving**.

---

## Sebelum serving, coba lihat pengalaman client kalau kita nggak punya API

Bayangin ada backend engineer yang cuma ingin tahu demand taxi untuk zone 161 jam 18:00.

Kalau kita belum punya serving layer, kita mungkin bilang:

> “Oke, load file model dulu. Habis itu cari demand tujuh hari terakhir, bikin lag 1 jam, 2 jam, 3 jam, 24 jam, 168 jam, bikin rolling mean, jangan lupa zone_id harus category, terus urutin column-nya persis seperti training, baru model.predict.”

Secara teknis bisa.

Tapi sekarang backend engineer harus ngerti:

- framework model kita;
- lokasi artifact;
- exact feature names;
- feature order;
- historical lookback;
- category dtype;
- leakage rule;
- model version yang approved.

Artinya internal implementation model bocor ke client.

Coupling-nya tinggi banget.

Kalau besok feature berubah sedikit, semua client ikut kena.

Nah, serving layer dibuat untuk **menyembunyikan complexity internal di balik interface yang stable**.

Client cukup bilang:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Lalu service kita yang tanggung jawab melakukan sisanya.

---

# Serving itu sebenarnya abstraction boundary

Kalau disederhanakan:

~~~text
CLIENT
"aku mau prediction zone 161 jam 18:00"
        ↓
        ↓ simple business request
        ↓
SERVING LAYER
- validate request
- cari historical demand
- bikin online features
- resolve champion model
- run inference
- log prediction
        ↓
        ↓ simple response
        ↓
CLIENT
"predicted demand = 147.8"
~~~

Client tidak perlu tahu model kita HistGradientBoosting, LSTM, XGBoost, atau besok ganti model lain.

Selama contract API tetap sama, internal implementation bisa berevolusi.

Ini salah satu software engineering principle yang sangat useful di ML system: **separate interface from implementation**.

---

# Kenapa request kita cuma zone_id dan target_datetime?

Ini design decision yang sengaja kita ambil.

Kita bisa saja bikin API seperti:

~~~json
{
  "zone_id": 161,
  "hour": 18,
  "day_of_week": 1,
  "lag_1h": 120,
  "lag_2h": 115,
  "lag_24h": 142,
  "lag_168h": 138,
  "rolling_mean_3h": 119.7,
  "rolling_mean_24h": 131.2
}
~~~

Kelihatannya gampang karena model tinggal predict.

Tapi siapa yang bikin feature itu?

Sekarang client.

Masalahnya:

- client harus ngerti logic feature engineering;
- client bisa salah hitung;
- client bisa accidentally leak target;
- semua client harus update kalau feature berubah;
- consistency training-serving jadi lebih susah.

Makanya kita pilih contract yang lebih dekat ke business problem:

~~~text
zone_id
target_datetime
~~~

Lalu serving layer yang bertanggung jawab membangun model input.

Pattern ini bikin responsibility lebih clear.

---

# Training-serving consistency

Ini salah satu problem paling berbahaya di production ML karena kadang nggak langsung kelihatan.

Misalnya saat training kita definisikan:

~~~text
rolling_mean_3h
=
mean demand dari 3 jam SEBELUM target
~~~

Target jam 18:00 berarti:

~~~text
15:00
16:00
17:00
~~~

Tapi online code accidentally menghitung:

~~~text
16:00
17:00
18:00
~~~

Sekarang feature serving punya informasi target hour.

Model offline terlihat bagus, online logic beda, dan hasil bisa misleading.

Atau kasus lain: training zone_id diperlakukan categorical, tapi serving kirim integer biasa dengan semantics berbeda.

Jadi kita butuh **training-serving consistency**:

> Feature yang dipakai saat inference harus punya arti, urutan, dan transformation yang sama dengan saat training.

Workshop kita menjaga ini lewat reusable Python logic, explicit feature contract, dan tests.

Production system yang lebih besar sering memakai feature store untuk membantu centralize feature definitions, tapi principle-nya sama.

---

# Online feature generation di project kita

Untuk target:

~~~text
2025-01-28 18:00
zone 161
~~~

serving layer perlu history seperti:

~~~text
lag_1h   → 17:00
lag_2h   → 16:00
lag_3h   → 15:00
lag_24h  → kemarin 18:00
lag_168h → minggu lalu 18:00
~~~

dan rolling feature dari data sebelum target.

Yang penting:

> **Target hour sendiri tidak boleh dibaca sebagai feature.**

Walaupun historical replay kita secara fisik mungkin sudah punya file full Jan 28, online feature provider tetap enforce timestamp strictly before target.

Ini reminder penting:

> MLOps tools tidak bisa menyelamatkan bad ML logic.

Kita bisa punya Airflow, MLflow, Docker, Grafana yang keren, tapi kalau leakage masih ada, system tetap salah.

---

# Model selection: jangan hard-code version

Misalnya registry punya:

~~~text
version 1
version 2
version 3
~~~

Kalau FastAPI hard-code:

~~~text
load version 3
~~~

maka setiap kali model baru dipromote:

~~~text
edit source code
commit
CI
build image
deploy
~~~

Padahal application behavior yang berubah cuma model selection.

Lebih clean:

~~~text
load alias "champion"
~~~

Alias adalah pointer.

Hari ini:

~~~text
champion → version 3
~~~

Besok:

~~~text
champion → version 5
~~~

API code tetap sama.

Ini memisahkan lifecycle application dan lifecycle model.

---

# Kenapa model tidak di-load ulang setiap request?

Bayangin ada 100 request.

Bad flow:

~~~text
request 1
→ query MLflow
→ download model
→ deserialize
→ predict

request 2
→ query MLflow
→ download model
→ deserialize
→ predict
~~~

Wasteful banget.

Loading model bisa jauh lebih mahal daripada inference.

Project kita pakai cache.

Flow-nya kurang lebih:

~~~text
first request
↓
resolve champion
↓
load model
↓
cache

next request
↓
reuse model

after refresh interval
↓
check alias again
↓
champion changed?
├── no  → keep cached model
└── yes → reload new version
~~~

Jadi kita balance freshness dan registry overhead.

---

# Prediction logging — kenapa prediction harus disimpan?

Sekarang kita predict:

~~~text
target 18:00
prediction = 147.8
~~~

Ground truth 18:00 belum ada saat prediction dibuat.

Beberapa waktu kemudian actual demand keluar:

~~~text
actual = 165
~~~

Kita ingin hitung error.

Tapi untuk itu kita harus ingat:

> “Model dulu predict berapa?”

Makanya successful prediction kita log.

Fields penting:

~~~text
logged_at
zone_id
target_datetime
predicted_trip_count
model_name
model_version
model_alias
run_id
~~~

Nanti model monitoring bisa join:

~~~text
prediction log
+
actual processed demand
↓
error
↓
MAE / RMSE
~~~

Kalau prediction tidak dicatat, future ground truth nggak punya pasangan.

---

# Kenapa JSONL?

Workshop pakai:

~~~text
data/monitoring/predictions.jsonl
~~~

JSONL = satu JSON object per line.

Kenapa bukan database?

Karena objective workshop adalah lifecycle MLOps, bukan database architecture.

JSONL cukup untuk append sederhana, inspect manual, replay evaluation, dan explain prediction event.

Production besar mungkin pakai Kafka, database, data warehouse, event store, atau observability pipeline.

Yang penting concept-nya:

> Prediction event harus bisa ditrace ke model version dan target.

---

# Negative prediction

Regression secara matematis bisa output negatif.

Taxi pickup count nggak mungkin negatif.

Serving layer apply domain constraint:

~~~text
max(0, prediction)
~~~

Ini contoh post-processing.

Post-processing juga bagian dari actual system behavior, jadi harus documented dan tested.

---

# Serving vs deployment — jangan ketuker

### Serving

> Gimana model menerima request dan mengembalikan prediction?

~~~text
FastAPI
~~~

### Deployment

> Gimana application serving dijalankan di environment tertentu?

~~~text
Docker
VM
Kubernetes
cloud service
~~~

Jadi:

~~~text
FastAPI
→ serving interface

Docker
→ runtime packaging

CI/CD
→ artifact delivery
~~~

Concern-nya beda.

---

# Kalau feature history belum ada gimana?

Misalnya client request target jam 18:00 tapi historical data untuk lag_168h belum lengkap.

Kita nggak isi random default dan nggak silently predict dengan feature incomplete.

Service reject request dengan error yang meaningful.

Karena **fail clearly lebih baik daripada produce confident-looking garbage prediction**.

---

# Checkpoint

Coba jawab pakai bahasa sendiri:

1. Kenapa client tidak kita suruh kirim lag feature?
2. Apa risiko training-serving inconsistency?
3. Kenapa model selection pakai champion alias?
4. Kenapa model di-cache?
5. Kenapa prediction logging penting?
6. Serving dan deployment beda apa?
7. Kalau history incomplete, kenapa lebih baik reject daripada predict asal?

Kalau jawabannya sudah kebayang, FastAPI section berikutnya tinggal implementation detail dari serving architecture ini.
