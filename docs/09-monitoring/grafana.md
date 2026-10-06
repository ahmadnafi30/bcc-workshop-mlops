# Grafana — Dari Metric Mentah Jadi Dashboard yang Bisa Dibaca Manusia
!!! tip "Grafana UI: baca panel sesuai sumber datanya"
    Buka [dashboard Taxi Demand MLOps](http://localhost:3000/d/taxi-demand-mlops/taxi-demand-mlops), pilih **Last 30 minutes**, lalu baca traffic/latency dan evaluasi model sebagai sinyal yang berbeda. Traffic memerlukan request prediction. MAE memerlukan actual, prediction yang cocok, dan evaluation job. Jadi dashboard bisa terbuka dengan benar sementara sebagian panel masih menunjukkan belum ada data.

    Ikuti [tur dashboard untuk pemula](../00-start-here.md#grafana-ui) atau [Quickstart Grafana](../10-hands-on/dashboard-quickstart.md) untuk menghasilkan data end-to-end.


Prometheus sudah punya time-series data.

Tapi kalau setiap kali mau inspect system kita harus buka Prometheus UI lalu ngetik query satu-satu, kurang nyaman.

Grafana masuk sebagai visualization layer.

Mental model yang paling gampang:

~~~text
Prometheus
→ collect + store + query

Grafana
→ visualize + dashboard
~~~

Grafana tidak menggantikan Prometheus.

Dia baca data dari Prometheus.

---

# Analogi control room

Prometheus seperti sensor + measurement database.

Grafana seperti layar control room.

Sensor tetap bisa collect data walaupun layar mati.

Sebaliknya, layar tanpa datasource juga nggak punya apa-apa buat ditampilkan.

Jadi dua role ini beda.

---

## Datasource

Grafana perlu tahu:

> “Data saya ambil dari mana?”

Project provision datasource:

~~~text
Prometheus
http://prometheus:9090
~~~

Kenapa hostname prometheus?

Karena Grafana jalan di Docker Compose network yang sama.

Jadi internal service discovery lagi.

---

# Provisioning — kenapa dashboard disimpan di Git?

Kita bisa bikin dashboard manual lewat UI.

Tapi bayangin presenter setup dashboard di laptop sendiri.

Workshop hari H:

~~~text
presenter
→ dashboard ada

participant
→ clone repo
→ dashboard kosong
~~~

Nggak reproducible.

Makanya project simpan configuration:

~~~text
monitoring/grafana/
├── provisioning/
└── dashboards/
~~~

Jadi:

~~~text
git clone
↓
docker compose up
↓
datasource auto-configured
↓
dashboard auto-loaded
~~~

Ini jauh lebih professional dan repeatable.

---

# Dashboard sebagai code/config artifact

Dashboard JSON memang bukan Python code, tapi dia tetap bagian system configuration.

Benefit kalau masuk Git:

- bisa review perubahan;
- punya history;
- reproducible;
- tidak tergantung klik manual;
- presenter dan participant dapat view yang sama.

Ini small example dari infrastructure/configuration as code mindset.

---

# Panel apa saja?

Dashboard starter kita punya:

~~~text
API request rate
API p95 latency
prediction count
retrain recommended
recent MAE
reference MAE
current model version
~~~

Kenapa metric operational dan model performance ditaruh satu tempat?

Biar kita cepat compare dua health dimension.

---

# Scenario 1 — service sehat, model jelek

Misalnya:

~~~text
p95 latency = 60 ms
HTTP success tinggi
request rate normal

recent MAE = naik jauh
~~~

Interpretation:

~~~text
operations
✅

model quality
❌
~~~

Action focus kemungkinan ke:

- data;
- model performance;
- retraining;
- drift investigation.

Restart API container belum tentu membantu.

---

# Scenario 2 — model sehat, service jelek

~~~text
recent MAE normal
reference MAE normal

p95 latency = 8 seconds
timeouts naik
~~~

Interpretation:

~~~text
model quality
✅

service performance
❌
~~~

Action focus:

- resource;
- network;
- concurrency;
- application bottleneck.

Retrain model bukan solusi.

---

# Scenario 3 — dua-duanya bermasalah

~~~text
latency naik
MAE naik
~~~

Sekarang kita perlu investigate dua layer.

Mungkin:

- new model lebih berat;
- infrastructure overloaded;
- data pipeline issue;
- recent model degraded.

Dashboard membantu narrow investigation, bukan otomatis memberi root cause.

---

# Dashboard kosong belum tentu Grafana broken

Kalau baru docker compose up dan belum ada request:

~~~text
request rate
→ zero / no samples
~~~

Normal.

Kita perlu traffic.

Command workshop:

~~~bash
uv run python scripts/generate_api_traffic.py \
  --date 2025-01-28 \
  --start-hour 17 \
  --end-hour 18
~~~

Script ini benar-benar call FastAPI lewat HTTP.

Supaya middleware metrics beneran triggered.

~~~text
request middleware
✅

request counter
✅

latency histogram
✅

prediction log
✅
~~~

Observability debugging juga perlu dependency thinking.

---

# generate_api_traffic vs replay_predictions

Ini penting karena dua script kelihatannya mirip.

## generate_api_traffic.py

Future extension:

~~~text
script
↓ HTTP POST
FastAPI
↓
prediction
~~~

Effect:

~~~text
API metrics
✅

prediction log
✅
~~~

## replay_predictions.py

Flow:

~~~text
script
↓
predictor directly
~~~

Effect:

~~~text
API latency metrics
❌

prediction log
✅
~~~

Kenapa direct replay masih useful?

Karena buat batch evaluation, kita nggak selalu perlu overhead HTTP.

Jadi:

~~~text
API traffic generator
→ operational demo

direct replay
→ batch model evaluation
~~~

Different purpose.

---

# Recent MAE panel tidak muncul magically

Grafana tidak menghitung MAE dari raw prediction.

Chain lengkap:

~~~text
prediction request
↓
predictions.jsonl
↓
ground truth available
↓
evaluate_predictions.py
↓
performance_summary.json
↓
FastAPI /metrics
↓
Prometheus scrape
↓
Grafana query
↓
panel
~~~

Panjang ya?

Justru ini bagus.

Participant jadi lihat bahwa dashboard adalah ujung dari dependency chain, bukan sumber logic.

---

# Debugging panel kosong

Jangan langsung:

> “Grafana error.”

Debug chain.

## Step 1

Ada prediction log?

~~~text
data/monitoring/predictions.jsonl
~~~

## Step 2

Ground truth ada?

~~~text
data/processed/demand/...
~~~

## Step 3

Evaluation sudah dijalankan?

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

## Step 4

Summary ada?

~~~text
data/monitoring/performance_summary.json
~~~

## Step 5

FastAPI metrics expose value?

~~~text
/metrics
~~~

## Step 6

Prometheus target UP?

## Step 7

Prometheus query punya result?

## Step 8

Baru check Grafana panel.

Dependency-first debugging jauh lebih efektif daripada random restart.

---

# Refresh interval dan scrape delay

Misalnya summary file baru saja update.

Grafana belum tentu berubah instant.

Kenapa?

~~~text
summary file changes
↓
next /metrics scrape
↓
Prometheus stores sample
↓
next Grafana refresh
↓
panel updates
~~~

Ada small propagation delay.

Observability system juga punya latency.

---

# Grafana bukan decision engine

Kita sengaja tidak menaruh logic:

~~~text
if panel MAE > threshold:
    retrain
~~~

di dashboard.

Decision dibuat Python monitoring code.

Prometheus expose/store metric.

Grafana visualize.

Airflow orchestrate action.

Separation:

~~~text
calculation
→ monitoring code

time-series
→ Prometheus

visualization
→ Grafana

action
→ Airflow
~~~

Ini lebih mudah dites dan di-maintain.

---

# Dashboard design juga punya responsibility

Dashboard yang penuh 50 panel belum tentu lebih bagus.

Pertanyaan:

> “Apa decision yang ingin dibantu dashboard ini?”

Workshop dashboard intentionally simple.

Kita ingin participant bisa lihat:

1. traffic ada?
2. API lambat?
3. model version apa?
4. prediction count?
5. recent MAE vs reference?
6. retrain recommended?

Enough buat satu coherent operational story.

---

# Alerting — next step yang natural

Kalau metric sudah mature, kita bisa add alert.

Contoh:

~~~text
retrain_recommended = 1
↓
alert
↓
Slack / email / on-call
~~~

Tapi alerting punya own problem:

- false positive;
- threshold;
- duplicate alerts;
- alert fatigue;
- ownership.

Jadi jangan buru-buru alert kalau metric semantics belum solid.

Bad alert:

> “Something changed.”

Good alert:

> “Champion recent MAE melewati threshold selama window tertentu dan sample count cukup.”

Actionable context matters.

---

# Visualization bisa misleading

Y-axis scale, aggregation window, smoothing, dan time range bisa mengubah perception.

Misalnya MAE naik:

~~~text
10.0 → 10.3
~~~

Kalau Y-axis zoom 9.9–10.4, kelihatan dramatis.

Kalau Y-axis 0–100, kelihatan flat.

Dashboard bukan neutral truth. Cara visualisasi juga perlu sense.

Makanya numeric context dan threshold tetap penting.

---

# Checkpoint

Coba jawab:

1. Grafana dan Prometheus beda role apa?
2. Kenapa dashboard provisioning disimpan di Git?
3. Kenapa empty dashboard belum tentu error?
4. generate_api_traffic dan replay_predictions beda apa?
5. Recent MAE sampai Grafana lewat chain apa?
6. Kenapa retraining logic nggak ditaruh di Grafana?
7. Kenapa panel update bisa delay?
8. Dashboard yang lebih banyak panel belum tentu lebih bagus kenapa?
9. Kenapa alerting sebaiknya datang setelah metric semantics clear?

Kalau semua kebayang, dashboard bukan lagi sekadar “UI cantik”, tapi bagian dari observability architecture yang masuk akal.

---

## Sinyal dashboard yang dipakai repository ini

Konfigurasi panel ada di `monitoring/grafana/dashboards/taxi-mlops.json`. Angka-angka berikut mengikuti query dan exporter yang benar-benar ada di project:

| Panel | Cara membacanya |
| --- | --- |
| `Prediction Request Rate` | Request ke `/predict` per detik selama 1 menit terakhir, termasuk request yang gagal. Scrape `/metrics` dan health check tidak ikut dihitung. |
| `Prediction Latency` | p50 dan p95 durasi HTTP `/predict` selama 5 menit, termasuk waktu feature loading dan request gagal. |
| `Predictions in 5m` | Prediction API yang berhasil selama 5 menit. Request gagal dan `replay_predictions.py` tidak menambah counter API ini. |
| `Prediction 4xx Rejection Rate` / `Prediction 5xx Error Rate` | Proporsi request `/predict` yang ditolak atau gagal di service. Nilainya belum tersedia saat tidak ada traffic; nol berarti ada traffic tanpa error pada window tersebut. |
| `Evaluation Samples` | Jumlah prediction unik yang sudah cocok dengan actual, dibanding minimum sample. MAE tetap bisa terlihat ketika sample masih kurang, tetapi belum cukup untuk keputusan retraining. |

Model Evaluation Status memakai kode `0` untuk belum dievaluasi, `1` untuk sample belum cukup, `2` untuk masih dalam batas, dan `3` untuk perlu retrain. Jika actual belum tersedia atau summary belum ada, kualitas model belum diketahui; panel MAE menampilkan N/A, bukan nol.

Default evaluator memakai multiplier `1.25`, minimum `100` sample, dan paling banyak `500` prediction terbaru. Threshold-nya adalah `reference MAE × multiplier`. Nilai ini bisa diubah lewat opsi `--degradation-multiplier`, `--min-samples`, dan `--recent-limit` pada `scripts/evaluate_predictions.py`.

`Last Evaluation (NYC)` dan `Evaluation Age` mengikuti waktu nyata saat job evaluasi berjalan. `Latest Evaluated Replay Target (NYC)` menunjukkan target historis terakhir yang sudah punya actual; tanggal replay 2025 tetap wajar. Setelah promotion, `Serving Model (Last Prediction)` bisa berbeda dari `Evaluated Model` sampai prediction dan evaluasi untuk versi baru tersedia.
