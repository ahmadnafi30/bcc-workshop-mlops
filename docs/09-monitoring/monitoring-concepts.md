# Monitoring — API Cepat Belum Tentu Modelnya Masih Bagus

Sampai sini kita sudah punya model yang ditrain, diregister, diserve, dibungkus Docker, bahkan punya CI/CD.

Kalau berhenti di sini, project kelihatan complete.

Tapi ada satu pertanyaan besar:

> “Setelah system hidup beberapa hari, kita tahu semuanya masih sehat dari mana?”

Inilah alasan monitoring jadi bagian penting di MLOps.

Dan ML monitoring punya satu twist:

> **System bisa sehat secara software, tapi prediction quality-nya rusak.**

---

## Dua health dimension

Kita pisahkan minimal dua dimension.

## 1. System Health

Pertanyaan:

~~~text
API hidup?
latency berapa?
request banyak nggak?
error rate?
service reachable?
~~~

Ini classic operational monitoring.

## 2. Model Health

Pertanyaan:

~~~text
prediction masih akurat?
recent MAE naik?
model version mana yang lagi serve?
ground truth sudah cukup?
perlu retrain?
~~~

Dua-duanya penting.

---

# Kenapa harus dipisah?

Bayangin dashboard:

~~~text
HTTP 200 ✅
p95 latency 70 ms ✅
zero 5xx ✅
CPU normal ✅
~~~

Semua hijau.

Tapi ternyata:

~~~text
actual demand = 200
prediction = 80
~~~

dan ini terjadi berkali-kali.

Kalau kita hanya monitor server, kita akan bilang:

> “System sehat.”

Padahal dari sisi business prediction, system gagal.

Sebaliknya, model bisa sangat accurate tapi API timeout 15 detik.

Jadi:

~~~text
software health
≠
model health
~~~

Keduanya harus dipantau.

---

# Analogi restoran

Restaurant bisa serve sangat cepat, pelayan ramah, order masuk lancar, tapi kualitas makanannya menurun.

Operationally bagus. Product quality buruk.

Bisa juga makanannya enak, tapi customer harus menunggu satu jam.

Product quality bagus. Operations buruk.

Monitoring ML kurang lebih punya dua perspektif ini.

---

# Delayed ground truth — challenge unik ML

Kalau API biasa menerima request, kita langsung tahu response sukses atau gagal.

Tapi accuracy prediction sering baru diketahui nanti.

Contoh:

~~~text
17:00
model predict demand jam 18:00 = 147

18:00–18:59
real taxi pickups terjadi

setelah 19:00
actual demand jam 18:00 sudah complete
~~~

Jadi saat prediction dibuat, kita belum tahu error.

Model monitoring butuh dua tahap:

~~~text
prediction now
↓
save prediction

later
↓
actual ground truth arrives
↓
match prediction + actual
↓
calculate error
~~~

Ini alasan prediction logging sangat penting.

---

## Prediction log

Project simpan prediction ke:

~~~text
data/monitoring/predictions.jsonl
~~~

Isi penting:

~~~text
logged_at
zone_id
target_datetime
prediction
model_version
run_id
~~~

Kenapa model version dan run ID ikut disimpan?

Karena kalau model berubah di tengah periode, kita harus tahu prediction mana dibuat version mana.

Kalau hanya simpan angka prediction tanpa lineage, monitoring analysis jadi ambigu.

---

# Ground truth

Actual demand diambil dari processed hourly demand.

Conceptually:

~~~text
prediction:
zone 161
18:00
147

actual:
zone 161
18:00
165
~~~

Error:

~~~text
absolute_error = |147 - 165|
               = 18
~~~

Kita simpan detail evaluation ke:

Sekarang kita punya evidence per prediction.

Jadi summary MAE bukan black box. Kita masih punya row-level evidence.

---

# Kenapa MAE dan RMSE lagi?

Monitoring pakai metric yang sama dengan validation supaya comparison meaningful.

### MAE

Average absolute error.

Gampang interpret:

> “Model rata-rata meleset berapa pickup?”

### RMSE

Lebih sensitive ke large errors.

Kalau ada beberapa spike besar, RMSE bisa naik lebih cepat.

Keduanya memberi perspective berbeda.

---

# Recent window

Kenapa kita nggak hitung MAE dari seluruh history sejak hari pertama?

Bayangin model bagus selama 6 bulan, lalu 3 hari terakhir rusak.

All-time MAE bisa masih terlihat bagus karena history lama sangat banyak.

Kita lebih interested:

> “What is happening recently?”

Makanya monitoring pakai recent window atau recent prediction limit.

Concept:

~~~text
all history
→ good for long-term reporting

recent window
→ good for detecting current degradation
~~~

---

## Reference MAE

Kita butuh pembanding.

Bad design:

~~~text
if recent_mae > 20:
    retrain
~~~

Kenapa 20?

Random.

Workshop kita ambil reference dari **champion validation MAE** di MLflow.

Arbitrary.

Kita anchor ke champion validation performance.

Example:

~~~text
champion validation MAE = 10
~~~

Default multiplier:

~~~text
1.25
~~~

Threshold:

~~~text
10 × 1.25 = 12.5
~~~

Kalau recent MAE lebih dari 12.5, kita mulai curiga degradation.

Ini relative threshold.

---

# Kenapa validation MAE jadi reference?

Validation metric adalah expectation quality model saat approved.

Kita tidak menganggap validation = production truth forever.

Tapi dia reasonable starting benchmark.

Kalau recent real-world-like performance jauh lebih buruk dari validation expectation, itu signal.

Production mature mungkin pakai:

- business SLO;
- per-segment threshold;
- rolling baseline;
- statistical test;
- confidence interval.

Workshop mulai dari rule yang mudah dipahami.

---

# Minimum sample — jangan panik karena satu outlier

Misalnya prediction pertama error-nya besar banget.

Harus langsung retrain?

Belum tentu.

Bisa event aneh, corrupted data point, atau one-off surge.

Makanya kita require minimum evaluated predictions.

Default:

~~~text
100 samples
~~~

Decision menjadi:

~~~text
recent MAE > threshold
AND
sample count >= minimum
~~~

Automation yang bagus bukan automation yang selalu cepat bereaksi.

Automation yang bagus juga tahu kapan evidence belum cukup.

---

# Performance summary

Project save summary:

~~~text
data/monitoring/performance_summary.json
~~~

Isi penting:

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

File ini jadi bridge antara evaluation logic dan metrics/orchestration.

---

# Monitoring pipeline vs dashboard

Jangan taruh decision logic di Grafana.

Flow yang sehat:

~~~text
monitoring code
→ calculate metric + recommendation

Prometheus
→ store time series

Grafana
→ visualize

Airflow
→ act on recommendation
~~~

Setiap component punya responsibility.

Kalau retraining logic ditaruh di dashboard query, governance dan testing jadi lebih sulit.

---

# Data drift vs performance degradation

Ini sering disamakan.

## Data Drift

Distribution input berubah.

Contoh:

~~~text
lebih banyak prediction malam
zone tertentu jadi jauh lebih sibuk
lag distribution berubah
~~~

## Performance Degradation

Error prediction memburuk.

~~~text
MAE naik
RMSE naik
~~~

Drift bisa terjadi tanpa accuracy drop.

Performance drop juga bisa terjadi tanpa obvious drift di feature yang kita monitor.

Workshop fokus ke performance monitoring karena ground truth tersedia.

Future extension bisa tambah Evidently atau custom drift analysis.

---

# Kenapa belum pakai Evidently?

Bukan karena tool-nya jelek.

Dedicated monitoring library useful.

Tapi kita ingin participant paham mechanics dulu:

~~~text
prediction
↓
ground truth
↓
join
↓
error
↓
aggregate
↓
decision
~~~

Kalau dari awal langsung pakai dashboard library, risk-nya participant tahu klik UI tapi nggak paham apa yang dihitung.

Concept first, tool later.

---

# Monitoring harus lead to action

Dashboard cantik saja belum close the loop.

Kita produce:

~~~text
retrain_recommended
~~~

Lalu Airflow monitoring DAG bisa consume signal itu.

Jadi:

~~~text
observe
↓
evaluate
↓
decide
↓
act
~~~

Itu feedback loop.

---

# What could go wrong?

## Ground truth belum datang

Recent MAE belum bisa dihitung.

Correct action:

~~~text
wait
~~~

Bukan assume zero error.

## Prediction log missing

Kita nggak bisa evaluate past prediction.

Observability gap.

## Model version campur

Kalau evaluation combine prediction dari v1 dan v2 tanpa filter, MAE summary misleading.

Makanya model version penting.

## Too-small sample

Noise bisa trigger retraining.

Makanya minimum sample.

---

# Checkpoint

Coba jawab:

1. System health dan model health bedanya apa?
2. Kenapa ground truth delayed?
3. Kenapa prediction harus disimpan sebelum actual ada?
4. Kenapa recent window useful?
5. Kenapa threshold relative lebih meaningful daripada angka random?
6. Kenapa minimum sample dibutuhkan?
7. Data drift dan performance degradation beda apa?
8. Kenapa Grafana bukan tempat retraining logic?

Kalau clear, Prometheus dan Grafana nanti tinggal jadi tools untuk observe signals yang sudah kita pahami.
