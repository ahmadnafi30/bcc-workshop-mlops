# Step 9 — Monitoring: Bikin Dashboard Bergerak dan Belajar Membaca Apa Artinya

Sekarang stack kita sudah hidup.

FastAPI bisa menerima prediction request.

Prometheus bisa scrape metric.

Grafana bisa render dashboard.

Tapi ada satu hal yang sering banget bikin bingung pas pertama belajar monitoring:

> “Kok dashboard-nya kosong? Berarti Grafana error ya?”

Belum tentu.

Dashboard hanya bisa menampilkan signal yang memang sudah diproduksi oleh system.

Kalau belum ada traffic, belum ada prediction, atau ground truth belum datang, beberapa panel memang seharusnya kosong atau zero.

Di step ini kita nggak cuma mau bikin graph bergerak. Kita mau ngerti **chain yang membuat graph itu bisa bergerak**.

---

## Goal

Setelah selesai, kalian harus bisa menjelaskan dua chain berbeda.

Operational monitoring:

~~~text
HTTP request
↓
FastAPI middleware
↓
Prometheus metric
↓
Prometheus scrape
↓
Grafana panel
~~~

Model performance monitoring:

~~~text
prediction
↓
prediction log
↓
ground truth datang belakangan
↓
evaluation
↓
performance summary
↓
FastAPI metrics endpoint
↓
Prometheus
↓
Grafana
~~~

Kenapa dua chain?

Karena latency bisa diketahui langsung saat request selesai, tapi prediction accuracy baru diketahui setelah actual target tersedia.

---

## 1. Buka Grafana sebelum generate traffic

Open:

~~~text
http://localhost:3000
~~~

Cari dashboard:

~~~text
MLOps / Taxi Demand MLOps
~~~

Lihat panel.

Beberapa mungkin:

~~~text
0
no data
flat
~~~

Jangan buru-buru restart Grafana.

Tanya:

> “Event yang mau diukur memang sudah terjadi belum?”

Kalau belum ada prediction request, prediction counter zero itu benar.

Kalau belum ada evaluation, recent MAE belum punya value juga benar.

Monitoring yang bagus tidak mengarang data supaya dashboard terlihat cantik.

---

## 2. Sebelum Grafana, cek Prometheus target

Open:

~~~text
http://localhost:9090
~~~

Masuk ke Targets.

Target API harus:

~~~text
UP
~~~

Kenapa kita cek ini di awal?

Karena dependency-nya:

~~~text
FastAPI /metrics
↓
Prometheus scrape
↓
Grafana
~~~

Kalau Prometheus bahkan nggak bisa scrape FastAPI, debug Grafana dulu itu salah layer.

Ini recurring debugging principle:

> **Start from the earliest broken dependency, not from the prettiest UI.**

---

## 3. Buka raw /metrics

Open:

~~~text
http://localhost:8000/metrics
~~~

Output-nya raw text.

Kelihatan nggak friendly.

Normal.

Endpoint ini primarily buat Prometheus.

Cari:

~~~text
taxi_api_requests_total
taxi_api_request_duration_seconds
taxi_predictions_total
~~~

Coba observe label-nya.

Misalnya request metric punya dimension method, path, status.

Sekarang kalian bisa connect:

~~~text
Python metric definition
↓
/metrics exposition
↓
Prometheus series
~~~

---

## 4. Predict dulu apa yang akan terjadi sebelum generate traffic

Kita akan run:

~~~bash
uv run python scripts/generate_api_traffic.py   --date 2025-01-28   --start-hour 17   --end-hour 18
~~~

Sebelum Enter, coba jawab:

1. Script ini call predictor langsung atau lewat HTTP?
2. Berapa jam target yang dikirim?
3. Apakah prediction log akan bertambah?
4. Apakah API request counter akan bertambah?
5. Apakah latency histogram akan punya observation baru?

Expected:

~~~text
HTTP
2 target hours
yes
yes
yes
~~~

Baru run.

---

## 5. Apa yang dilakukan generate_api_traffic.py?

Actual script:

~~~text
load Manhattan zone IDs
↓
for hour 17..18
↓
for each zone
↓
POST /predict
↓
count success / failed
~~~

Jadi jumlah request kira-kira:

~~~text
number_of_manhattan_zones × 2
~~~

Ini bukan random fake metric injection.

Kita benar-benar exercise FastAPI serving path.

---

## 6. Watch success dan failed

Terminal akan report:

~~~text
success
failed
target api
~~~

Kalau failed banyak, jangan lanjut seolah semuanya baik.

Read response.

Possible reason:

- champion belum ada;
- history tidak lengkap;
- API URL salah;
- service down;
- request invalid.

Operational monitoring demo harus mulai dari request yang memang berhasil.

---

## 7. Kenapa script ini berbeda dari replay_predictions.py?

Ini penting.

### generate_api_traffic.py

~~~text
script
↓ HTTP
FastAPI
↓
predictor
~~~

Effect:

~~~text
request counter ✅
latency histogram ✅
prediction counter ✅
prediction log ✅
~~~

### replay_predictions.py

~~~text
script
↓
predictor directly
~~~

Effect:

~~~text
request counter ❌
HTTP latency ❌
prediction log ✅
~~~

Kenapa direct replay masih useful?

Kalau kita mau batch historical evaluation, HTTP overhead bisa unnecessary.

Jadi:

~~~text
API traffic generator
→ operational monitoring demo

direct replay
→ batch model evaluation
~~~

Satu project bisa punya dua path yang sengaja berbeda.

---

## 8. Query raw counter

Di Prometheus query:

~~~text
taxi_api_requests_total
~~~

Observe value.

Ini cumulative counter.

Question:

> “Kalau total requests sudah 1000, apakah traffic saat ini tinggi?”

Belum tentu.

1000 bisa terkumpul selama seminggu.

Makanya counter sendiri belum jawab current traffic speed.

---

## 9. Query rate

Try:

~~~text
sum(rate(taxi_api_requests_total[1m]))
~~~

Sekarang kita estimate seberapa cepat counter bertambah dalam recent one-minute window.

Query di atas mencakup seluruh path API, termasuk request ke `/metrics` dari Prometheus. Untuk membaca traffic prediksi seperti panel **Prediction Request Rate** di Grafana, filter path `/predict`:

~~~text
sum(rate(taxi_api_requests_total{path="/predict"}[1m]))
~~~

Request scrape atau health check tidak membuktikan peserta sudah mengirim prediksi. Untuk checkpoint traffic, gunakan query yang memfilter `/predict` dan cek prediction log.

Analogy:

~~~text
counter
→ odometer

rate(counter)
→ speedometer
~~~

Odometer bilang total perjalanan.

Speedometer bilang current speed.

Ini salah satu mental model Prometheus paling useful.

---

## 10. Latency dan p95

Dashboard punya p95 latency.

Kenapa p95?

Bayangin:

~~~text
95 requests = 50 ms
5 requests = 4 sec
~~~

Kalau cuma average, tail problem bisa kelihatan lebih kecil.

p95 roughly bertanya:

> “95% request selesai di bawah sekitar berapa lama?”

Tail latency penting karena user yang unlucky tetap merasakan slow response.

---

## 11. Refresh Grafana

Wait beberapa detik buat:

~~~text
FastAPI metric update
↓
Prometheus scrape
↓
Grafana refresh
~~~

Sekarang request rate dan latency harus mulai punya signal.

Kalau belum, debugging order:

~~~text
generate script success?
↓
/metrics value changed?
↓
Prometheus target UP?
↓
Prometheus query has data?
↓
Grafana datasource/panel query?
~~~

Jangan random restart seluruh stack.

---

## 12. Sekarang pindah ke model monitoring

Operational metric bergerak.

Tapi kita belum menjawab:

> “Prediction-nya bagus nggak?”

Untuk itu, buka:

~~~text
data/monitoring/predictions.jsonl
~~~

Lihat beberapa entries.

Fields penting:

~~~text
logged_at
zone_id
target_datetime
predicted_trip_count
model_version
run_id
~~~

---

## 13. Kenapa model_version harus ikut di prediction log?

Bayangin setengah hari pertama champion v1.

Siang hari champion pindah v2.

Kalau log cuma simpan:

~~~text
target
prediction
~~~

nanti kita nggak tahu prediction buruk berasal dari model mana.

Model version adalah bagian dari prediction lineage.

---

## 14. Ground truth harus tersedia

Prediction untuk Jan 28 hanya bisa dievaluate kalau processed actual demand Jan 28 tersedia.

Check:

~~~text
data/processed/demand/2025-01-28.parquet
~~~

Kalau file belum ada, run daily replay Jan 28 dulu.

Ini penting secara semantics:

~~~text
missing ground truth
≠
zero error
~~~

Kalau actual belum ada, kita belum tahu model benar atau salah.

---

## 15. Run evaluate_predictions.py

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

Actual flow:

~~~text
resolve current champion
↓
ambil champion validation MAE
↓
load prediction log
↓
filter prediction by champion model version
↓
join with ground truth
↓
calculate absolute/squared errors
↓
take recent evaluation window
↓
calculate MAE/RMSE
↓
compare threshold
↓
write artifacts
~~~

Banyak ya?

Makanya model monitoring bukan sekadar satu Prometheus query.

---

## 16. Kenapa filter by model version?

Suppose:

~~~text
v1 predictions = 300
v2 predictions = 200
~~~

Kalau dicampur:

~~~text
recent MAE
~~~

jadi mixture dua model.

Kalau kita sedang evaluate champion v2, summary tersebut misleading.

Lineage membantu monitoring tetap model-specific.

---

## 17. Baca terminal output

Output punya bentuk seperti:

~~~text
model version: ...
evaluated: ...
reference MAE: ...
recent MAE: ...
threshold MAE: ...
retrain recommended: ...
~~~

Exact numeric values tergantung actual run.

Jangan hafal angka contoh dari docs.

Yang perlu dipahami relationship:

~~~text
recent_mae
vs
threshold_mae
~~~

dan:

~~~text
evaluation_count
vs
min_samples
~~~

---

## 18. Buka evaluations.parquet

Path:

~~~text
data/monitoring/evaluations.parquet
~~~

Optional inspect:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/monitoring/evaluations.parquet'); print(df.head()); print(df.shape)"
~~~

Cari:

~~~text
predicted_trip_count
actual_trip_count
absolute_error
squared_error
~~~

Ini row-level evidence di balik summary.

Kalau MAE terlihat aneh, kita bisa inspect individual errors.

---

## 19. Buka performance_summary.json

~~~text
data/monitoring/performance_summary.json
~~~

Fields:

~~~text
evaluation_count
recent_mae
recent_rmse
reference_mae
threshold_mae
retrain_recommended
latest_target_datetime
model_version
~~~

Question:

> “Kalau retrain_recommended false, monitoring gagal?”

No.

Bisa berarti champion masih healthy.

No action adalah valid outcome.

---

## 20. Bagaimana summary masuk ke Prometheus?

FastAPI metrics endpoint refresh model-performance gauge dari summary file saat scrape.

Flow:

~~~text
performance_summary.json
↓
FastAPI /metrics
↓
Prometheus scrape
↓
taxi_model_recent_mae
taxi_model_reference_mae
taxi_model_retrain_recommended
~~~

Grafana tidak membaca JSON langsung.

Ini dependency chain penting.

---

## 21. Refresh Grafana lagi

Setelah evaluation dan next scrape, panel recent MAE/reference MAE seharusnya mulai muncul kalau ada evaluated samples.

Kalau kosong:

~~~text
summary recent_mae null?
↓
/metrics expose gauge?
↓
Prometheus query punya value?
↓
Grafana panel?
~~~

Debug step by step.

---

## 22. Scenario game — diagnose layer-nya

### Scenario A

~~~text
p95 latency = 60 ms
HTTP success normal
recent MAE jauh naik
~~~

Interpretasi:

~~~text
service health
✅

model quality
❌
~~~

Potential investigation:

- data quality;
- distribution shift;
- model aging;
- retraining.

Restart Grafana bukan solution.

### Scenario B

~~~text
recent MAE normal
p95 latency = 8 sec
timeout naik
~~~

Interpretasi:

~~~text
model quality
✅

service performance
❌
~~~

Retraining model bukan first action.

### Scenario C

~~~text
request rate zero
all service healthy
~~~

Mungkin memang nggak ada traffic.

Zero traffic bukan otomatis incident.

### Scenario D

~~~text
Prometheus target DOWN
Grafana stale
~~~

Investigate API/network/scrape config before dashboard.

---

## 23. Cardinality thought experiment

Bayangin kita tambahkan label:

~~~text
request_id = unique UUID
~~~

Setiap request menghasilkan combination baru.

Prometheus bisa punya sangat banyak series.

Itu high cardinality.

Bandingkan:

### Bounded-ish labels

~~~text
method
path category
HTTP status
model version
~~~

### Dangerous unbounded labels

~~~text
request_id
user_id
free text
full timestamp
dynamic URL ID
~~~

Detailed individual info cocok di logs/events, bukan metric labels.

---

## 24. Unknown vs zero

Ini subtle tapi penting.

Case ground truth belum ada.

Wrong:

~~~text
error = 0
~~~

Itu berarti model perfect.

Correct:

~~~text
error = unknown / not evaluated
~~~

Dalam data system:

> Missing dan zero punya semantics berbeda.

Kalau kita salah represent missing sebagai zero, monitoring terlihat lebih bagus dari reality.

---

## 25. Monitoring detects symptom, not necessarily root cause

MAE naik adalah symptom.

Possible causes:

- data drift;
- data corruption;
- feature pipeline bug;
- extraordinary event;
- model aging;
- target definition change.

Monitoring bilang:

> “Something deserves investigation.”

Bukan:

> “Pasti retrain.”

Ini kenapa Step 10 masih punya governance boundary.

---

## 26. Experiment dengan policy

Script support:

~~~text
--degradation-multiplier
--min-samples
--recent-limit
~~~

Untuk learning, coba:

~~~bash
uv run python scripts/evaluate_predictions.py --min-samples 10
~~~

Lihat recommendation.

Lalu compare default 100.

Pertanyaan:

> “Mana yang lebih benar?”

Tidak ada universal answer.

Policy tergantung risk, noise, business cost, dan data volume.

Workshop goal-nya memahami sensitivity.

---

## 27. Propagation delay

Suppose performance_summary baru diupdate.

Grafana mungkin belum instant berubah.

Chain:

~~~text
file updated
↓
next /metrics scrape
↓
Prometheus stores sample
↓
next Grafana refresh
↓
panel changes
~~~

Ada small propagation delay.

Jadi jangan spam refresh dan conclude failure dalam 100 ms.

Observability system juga punya latency.

---

## 28. Monitoring chain recap

Operational:

~~~text
HTTP request
↓
middleware
↓
metrics
↓
Prometheus
↓
Grafana
~~~

Model:

~~~text
prediction
↓
prediction log
↓
actual later
↓
evaluation
↓
summary
↓
metrics
↓
Prometheus
↓
Grafana
~~~

Model chain lebih panjang karena ground truth delayed.

---

### Direct replay: apa bedanya

Coba jawab tanpa lihat docs:

1. Kenapa empty dashboard belum tentu error?
2. Prometheus target UP artinya apa?
3. generate_api_traffic beda apa dengan replay_predictions?
4. Counter beda apa dengan rate?
5. Kenapa p95 useful?
6. Kenapa prediction log simpan model_version?
7. Kenapa ground truth delayed?
8. Missing ground truth kenapa tidak boleh dianggap zero error?
9. Kenapa evaluation filter model version?
10. performance_summary sampai Grafana lewat chain apa?
11. retrain_recommended false bisa jadi success kenapa?
12. MAE naik berarti pasti drift nggak?
13. High-cardinality label itu apa?
14. Kalau panel kosong, debugging order yang masuk akal bagaimana?
15. Kenapa dashboard punya propagation delay?

Kalau semua kebayang, kalian bukan cuma “bisa pakai Grafana”. Kalian ngerti observability architecture di balik panel.

Next kita tutup loop dengan retraining.

---

### Urutan demo untuk dashboard repository ini

Kalau data, model, dan service belum disiapkan, mulai dari [Quickstart Grafana dari kondisi kosong](dashboard-quickstart.md). Quickstart menyiapkan training, champion, HTTP traffic, dan evaluasi.

Setelah prediction API menghasilkan log dan actual demand tersedia, jalankan:

~~~bash
uv run python scripts/evaluate_predictions.py
~~~

Periksa `evaluation_status` di output dan `data/monitoring/performance_summary.json`. Untuk memperagakan status sample belum cukup, jalankan ulang dengan `--min-samples 100000` setelah ada prediction yang cocok dengan actual, lalu kembalikan ke default dengan menjalankan command tanpa opsi tersebut. Tanpa matched sample, status tetap belum dievaluasi.

Dashboard memakai dua identitas model: serving version dari prediction API terakhir dan evaluated version dari summary MAE. Keduanya boleh berbeda sesudah promotion. Dashboard juga memakai dua clock: waktu nyata job evaluasi dan tanggal target replay historis di timezone `America/New_York`.
