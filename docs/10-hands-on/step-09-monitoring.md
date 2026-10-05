# Step 9 — Monitoring: Bikin Dashboard Benar-Benar Bergerak

Sekarang stack hidup.

Prometheus dan Grafana ada.

Tapi dashboard tanpa traffic ya kosong.

Kita generate real API traffic dan kemudian evaluate model quality.

---

## Goal

Setelah step ini:

- API operational metrics bergerak,
- Prometheus query works,
- Grafana dashboard punya data,
- prediction log dievaluate,
- recent MAE muncul,
- kalian ngerti system vs model monitoring.

---

## 1. Open Grafana sebelum traffic

~~~text
http://localhost:3000
~~~

Dashboard mungkin mostly zero/empty.

Ini bagus buat comparison before-after.

Jika belum pernah menjalankan evaluasi, **Model Evaluation Status** menunjukkan
**Belum dievaluasi** dan MAE belum tersedia. Kalau sudah ada summary dari demo
sebelumnya, periksa **Last Evaluation** dan **Evaluated Model** terlebih dahulu.

Panel **Prediction Request Rate** hanya menghitung `/predict`. Refresh dashboard
dan scrape `/metrics` sendiri tidak menambah prediction traffic.

---

## 2. Generate HTTP traffic

### Jalur manual kalau data dan model belum ada

Ikuti [Quickstart Grafana dari kondisi kosong](dashboard-quickstart.md). Panduan
tersebut memuat setup service, persiapan data, training, registration, promotion,
HTTP traffic, dan evaluasi tanpa Airflow. Setelah selesai, lanjutkan membaca
panel serta latihan monitoring di halaman ini.

### Jalur Airflow kalau training sudah selesai

Pastikan champion tersedia. Jika history Jan 27 belum ada, jalankan DAG
`taxi_daily_replay` dengan `replay_date=2025-01-27` terlebih dahulu. Setelah selesai,
jalankan untuk `replay_date=2025-01-28` dan tunggu sampai selesai. History per jam
sampai Jan 28 dibutuhkan untuk request jam 17–18.

Workshop ini melakukan replay setelah daily file tersedia. Feature provider
tetap membatasi history sebelum target hour, sedangkan actual pada target hour
dipakai nanti untuk evaluasi.

### Kirim request lewat API

Gunakan command ini setelah memilih salah satu jalur di atas:

~~~bash
uv run python scripts/generate_api_traffic.py \
  --date 2025-01-28 --start-hour 17 --end-hour 18
~~~

Script ini call FastAPI.

Kenapa bukan direct predictor?

Karena kita pengen exercise:

~~~text
HTTP middleware
request count
latency
prediction log
~~~

---

## 3. Refresh Grafana

Wait beberapa detik buat Prometheus scrape.

Lihat:

- request rate,
- p95 latency,
- prediction count,
- Serving Model (Last Prediction),
- 4xx rejection rate dan 5xx error rate.

Tunggu setidaknya dua scrape agar rate mulai tersedia. Error rate bisa bernilai
nol saat ada traffic tanpa error; saat tidak ada traffic, panel bisa belum
tersedia.

Kalau burst pertama selesai sebelum counter sempat di-scrape, rate dan increase
bisa masih nol. Tunggu 10–15 detik lalu jalankan script traffic sekali lagi agar
Prometheus menangkap pertambahan counter.

Untuk mencoba request ditolak, kirim body berikut melalui Swagger `/predict`:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:30:00"
}
~~~

Response seharusnya 422. Panel 4xx bergerak setelah scrape, tetapi counter
prediction berhasil tidak bertambah. Buka description panel untuk melihat
perbedaan antara request rate, rejection rate, dan prediction count.

Question:

> “Kalau request rate belum naik, chain mana yang mungkin belum jalan?”

Traffic → API → metrics → Prometheus → Grafana.

Debug from left to right.

---

## 4. Open Prometheus

~~~text
http://localhost:9090
~~~

Query:

~~~text
taxi_api_requests_total
~~~

Lihat raw series.

Then:

~~~text
sum(rate(taxi_api_requests_total{path="/predict"}[1m]))
~~~

Apa bedanya?

Counter vs rate.

---

## 5. Check prediction log

~~~text
data/monitoring/predictions.jsonl
~~~

Sekarang banyak entries.

Tapi belum otomatis punya actual error.

Need ground truth match.

---

## 6. Evaluate predictions

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

Observe terminal.

Expected summary fields:

~~~text
reference MAE
recent MAE
threshold
evaluation count
minimum samples
evaluation status
evaluated at
latest replay target
retrain recommended
~~~

---

## 7. Open performance summary

~~~text
data/monitoring/performance_summary.json
~~~

Read values.

Tanya:

> “Kalau retrain_recommended false, apakah monitoring gagal?”

No.

Lihat juga `evaluation_status`. `retrain_recommended=false` bisa berarti belum
ada actual, sample masih kurang, atau model berada dalam batas. Ketiganya punya
arti berbeda.

---

## 8. Refresh Grafana

Wait scrape.

Recent MAE dan reference MAE harus mulai muncul kalau evaluation available.

Perhatikan juga:

- **Model MAE**: recent, reference, dan garis threshold retraining.
- **Evaluation Samples**: jumlah match dibanding minimum.
- **Model Evaluation Status**: keputusan berdasarkan sample dan threshold.
- **Last Evaluation / Evaluation Age**: kapan job terakhir berjalan.
- **Latest Evaluated Replay Target**: target historical terakhir, ditampilkan dalam waktu NYC.
- **Evaluated Model**: model sumber MAE, yang perlu dibandingkan dengan Serving Model.

Untuk mendemokan sample belum cukup tanpa mengganti data atau model:

~~~bash
uv run python scripts/evaluate_predictions.py --min-samples 100000
~~~

Jika sudah ada match, status berubah menjadi **Sampel belum cukup**. MAE tetap
terlihat tetapi belum digunakan untuk merekomendasikan retraining. Setelah itu
kembalikan konfigurasi default:

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

Dashboard memakai timezone `America/New_York`. Tahun 2025 di panel target replay
normal, sementara waktu job evaluasi menunjukkan saat workshop berlangsung.

---

## 9. Operational vs model scenario

Coba discuss:

### Scenario 1

~~~text
p95 latency low
HTTP success
recent MAE high
~~~

Action focus model.

### Scenario 2

~~~text
recent MAE normal
p95 latency huge
~~~

Action focus service/infrastructure.

Monitoring membantu classify problem.

Saat model dipromote, kirim prediction baru lalu bandingkan dua tabel versi.
Serving bisa sudah memakai model baru sementara summary evaluasi masih berasal
dari model sebelumnya. Evaluasi berikutnya memakai champion baru dan menunggu
actual dari prediction model tersebut.

---

## 10. Direct replay distinction

Ada:

~~~text
replay_predictions.py
~~~

Ini direct predictor, useful buat fast batch model evaluation.

Tapi bypass HTTP.

Jadi jangan expect API latency panel bergerak kalau pakai script itu.

Use correct tool for intended signal.

---

## Mini challenge

Kenapa prediction detail nggak dimasukkan semua sebagai Prometheus labels?

Cardinality.

Detailed event → log/table.

Aggregate metric → Prometheus.

---

## Checkpoint

1. Scrape itu apa?
2. Counter vs rate?
3. p95 latency?
4. Prediction log kenapa perlu?
5. Ground truth datang kapan?
6. Model healthy vs service healthy beda apa?
7. retrain_recommended false bisa jadi success nggak?
8. Apa bedanya belum dievaluasi, sample kurang, dan dalam batas?
9. Kenapa tanggal replay berbeda dengan waktu job evaluasi?
