# Monitoring — API Sehat Belum Tentu Model Sehat

## Ini salah satu bagian paling penting di MLOps

Kita sudah:

- train,
- register,
- serve,
- containerize.

Apakah selesai?

Belum.

Karena setelah model hidup di luar validation set, kita masuk environment yang terus berubah.

Kita perlu feedback.

---

# Dua jenis health

## System health

Pertanyaan:

~~~text
API hidup?
latency berapa?
error rate?
berapa request?
~~~

Ini operational monitoring.

## Model health

Pertanyaan:

~~~text
prediction masih akurat?
recent MAE naik?
model version mana?
perlu retrain?
~~~

Ini model performance monitoring.

---

# Kenapa harus dipisah?

Bayangin case:

~~~text
HTTP 200
latency 40 ms
zero server errors
~~~

Operationally perfect.

Tapi model predict:

~~~text
actual 200
prediction 80
~~~

berulang-ulang.

API cepat.

Model jelek.

Jadi dashboard “all green” server belum cukup.

---

# Case sebaliknya

Model secara statistik masih bagus.

Tapi API latency 20 detik.

Client timeout.

Model good.

Service bad.

Itu juga problem.

---

# Restaurant analogy

Operational monitoring:

> “Restorannya buka? Pesanan datang cepat?”

Model monitoring:

> “Makanannya masih enak?”

Restaurant bisa cepat serve makanan nggak enak.

Bisa juga makanan enak tapi pelanggan tunggu satu jam.

Dua kualitas berbeda.

---

# Delayed ground truth

ML monitoring punya challenge unik.

Saat predict 18:00 di 17:00:

~~~text
prediction exists
actual does not exist yet
~~~

Ground truth baru complete setelah target hour selesai.

Jadi performance monitoring naturally delayed.

Flow:

~~~text
predict now
↓
log prediction
↓
wait until actual available
↓
join prediction + actual
↓
calculate error
~~~

---

# Prediction log

Kita simpan:

~~~text
data/monitoring/predictions.jsonl
~~~

Fields:

~~~text
logged_at
zone_id
target_datetime
predicted_trip_count
model_name
model_version
run_id
~~~

Tanpa log ini kita kehilangan historical prediction.

---

# Evaluation table

Saat actual processed demand tersedia:

~~~text
prediction
+
actual
↓
absolute_error
squared_error
~~~

Save:

~~~text
data/monitoring/evaluations.parquet
~~~

---

# Performance summary

Output:

~~~text
data/monitoring/performance_summary.json
~~~

Isi:

- recent MAE,
- recent RMSE,
- reference MAE,
- threshold,
- sample count,
- latest target,
- retrain recommendation.

---

# Reference MAE

Kita nggak pakai arbitrary:

~~~text
if MAE > 20:
  retrain
~~~

Kita ambil champion validation MAE dari MLflow.

Misalnya:

~~~text
reference MAE = 10
multiplier = 1.25

threshold = 12.5
~~~

Kalau recent MAE > 12.5 dan sample cukup, recommend retrain.

---

# Why relative threshold?

Karena scale problem beda-beda.

MAE 20 bisa terrible di satu task, normal di task lain.

Relative threshold anchor ke known champion quality.

---

# Minimum sample

Suppose satu prediction punya error besar.

Haruskah langsung retrain?

Probably no.

Could be outlier.

Makanya:

~~~text
min_samples = 100
~~~

Decision hanya valid setelah enough evidence.

---

# Window

Kita pakai recent latest predictions dengan limit.

Kenapa nggak all history?

Karena kita interested in **recent behavior**.

All-time MAE bisa hide recent degradation.

---

# Drift vs degradation

Ini juga sering ketuker.

## Data drift

Input distribution berubah.

Contoh:

~~~text
hour distribution
zone traffic distribution
~~~

## Performance degradation

Prediction error memburuk.

Drift bisa terjadi tanpa performance drop.

Performance drop bisa terjadi tanpa obvious feature drift.

Workshop directly monitor performance karena ground truth tersedia.

---

# Kenapa belum Evidently?

Bisa banget jadi extension.

Tapi core workshop cukup dengan:

- prediction logging,
- actual matching,
- MAE/RMSE,
- threshold.

Kita ingin understand principle sebelum add dedicated drift tool.

---

# Monitoring should lead to action

Dashboard cantik tanpa action logic kurang useful.

Kita connect monitoring ke:

~~~text
retrain_recommended
~~~

Lalu Airflow monitoring DAG consume decision.

Ini menutup feedback loop.

---

# Takeaway

Operational monitoring menjawab:

> “Can the system serve?”

Model monitoring menjawab:

> “Should we still trust the predictions?”

Keduanya harus ada.
