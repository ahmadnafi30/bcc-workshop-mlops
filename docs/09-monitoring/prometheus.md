# Prometheus — Ngumpulin Metric System Secara Time-Series

FastAPI sekarang sudah expose metric.

Pertanyaan berikutnya:

> “Siapa yang ngumpulin metric itu dari waktu ke waktu?”

Prometheus.

Prometheus adalah monitoring system yang fokus pada **numeric time-series**. Jadi bukan cuma “lihat angka sekarang”, tapi juga melihat bagaimana angka itu berubah dari waktu ke waktu.

---

# Pull model

Prometheus biasanya **scrape** target.

~~~text
Prometheus
    ↓ HTTP GET
FastAPI /metrics
~~~

Setiap interval tertentu:

~~~text
scrape
↓
store sample
↓
repeat
~~~

Service kita tidak harus aktif push metric ke Prometheus. Dia cukup expose endpoint yang bisa dibaca.

---

# Apa itu scrape?

Scrape = Prometheus datang ke endpoint metric dan mengambil current values.

Kalau scrape interval 5 detik:

~~~text
12:00:00 → scrape
12:00:05 → scrape
12:00:10 → scrape
~~~

Setiap sample punya timestamp.

Karena itu Prometheus bisa jawab pertanyaan seperti:

> “Latency lima menit terakhir naik nggak�

> “Request rate sekarang berapa?”

> “Recent MAE tadi pagi dan sekarang beda nggak?”

---

# Counter

Counter cocok untuk jumlah event cumulative.

Contoh:

~~~text
taxi_api_requests_total
~~~

Nilainya:

~~~text
1
2
3
4
...
~~~

Counter biasanya naik terus sampai process restart.

Pertanyaan yang cocok:

> “Total request sejak process start berapa?”

Tapi kalau kita mau tahu traffic **sekarang**, raw counter kurang helpful.

Kita butuh rate.

---

# Counter vs rate — Sample Odometer dan Speedometer

Counter itu seperti odometer mobil:

~~~text
total distance travelled
~~~

Rate itu seperti speedometer:

~~~text
berapa cepat sekarang
~~~

Prometheus query:

~~~text
taxi_api_requests_total
~~~

menunjukkan cumulative count.

Sedangkan:

~~~text
rate(taxi_api_requests_total[1m])
~~~

mengestimasi kecepatan counter bertambah dalam recent window.

Ini distinction yang sangat useful.

---

# Gauge

Gauge bisa naik dan turun.

Contoh:

~~~text
taxi_model_recent_mae
~~~

Hari ini:

~~~text
10.4
~~~

Nanti:

~~~text
12.1
~~~

Besok:

~~~text
11.6
~~~

Gauge cocok buat current state yang memang bisa berubah dua arah.

Contoh lain:

- queue size;
- temperature;
- active connection;
- current memory usage.

---

# Histogram

Latency nggak cukup direpresentasikan satu angka average.

Bayangin:

~~~text
95 request = 50 ms
5 request  = 5 seconds
~~~

Average bisa terlihat masih lumayan, padahal beberapa user ngerasain latency parah.

Histogram merekam observations ke buckets.

Dari situ kita bisa estimate percentile.

---

# p50, p95, p99

## p50

Kurang-lebih median.

Bisa menggambarkan typical request.

## p95

95% request berada di bawah sekitar ini.

Tail latency mulai kelihatan.

## p99

Lebih fokus to extreme tail.

Di production, percentile sering lebih meaningful daripada average buat latency service.

Workshop kita pakai p95 supaya konsepnya gampang terlihat.

---

# Metric di project kita

Operational:

~~~text
taxi_api_requests_total
taxi_api_request_duration_seconds
taxi_predictions_total
taxi_prediction_trip_count
taxi_model_version_info
~~~

Model monitoring:

~~~text
taxi_model_recent_mae
taxi_model_reference_mae
taxi_model_retrain_recommended
taxi_model_evaluated_predictions
~~~

Perhatikan operational metric dan model metric bisa hidup di endpoint yang sama, tapi sumber maknanya beda.

---

# Labels

Metric bisa punya labels.

Contoh:

~~~text
method="POST"
path="/predict"
status="200"
~~~

Dengan label, kita bisa query lebih specific:

> “Berapa request POST /predict yang status 200?”

Powerful.

Tapi ada bahaya besar: **cardinality**.

---

# Cardinality

Setiap kombinasi label values berpotensi jadi time series berbeda.

Kalau label punya nilai tak terbatas:

~~~text
request_id
user_id
full timestamp
free-text error
dynamic URL ID
~~~

jumlah time series bisa meledak.

Misalnya 10 juta unique request_id.

Prometheus bukan tempat yang tepat untuk menyimpan semua detail individual request sebagai label.

---

# Kenapa path dinormalisasi?

Kalau API punya path dynamic:

~~~text
/users/1
/users/2
/users/3
...
~~~

dan semuanya dijadikan label raw, cardinality tumbuh terus.

Project kita hanya pakai known bounded paths.

Unknown path dinormalisasi jadi:

~~~text
other
~~~

Ini detail kecil, tapi menunjukkan observability juga butuh architecture decision.

---

# Kenapa zone_id nggak jadi label di semua metric?

Zone masih finite, tapi kita ingin ngajarin principle yang scalable.

Detail per entity sebaiknya dipikirkan matang.

Prometheus cocok buat aggregated time-series, bukan jadi replacement database prediction.

Kalau kita butuh row-level detail:

~~~text
prediction log
evaluation parquet
database
warehouse
~~~

lebih appropriate.

---

# Metrics vs Logs

Ini penting.

## Metrics

~~~text
numeric
aggregated
time-series
cheap to query trends
~~~

## Logs / Events

~~~text
detailed
individual record
rich context
~~~

Contoh:

~~~text
" berapa request per second?"
→ metric

" request tertentu pakai model version berapa?"
→ log/event
~~~

Observability system biasanya combine beberapa signal types.

---

# Scrape config di Compose

Prometheus target:

~~~text
api:8000
~~~

Kenapa bukan localhost?

Karena Prometheus ada di container.

Dari Prometheus container:

~~~text
localhost
= Prometheus container sendiri
~~~

FastAPI service bernama:

~~~text
api
~~~

Jadi Compose DNS dipakai lagi.

---

# Prometheus UI

Open:

~~~text
http://localhost:9090
~~~

Query pertama:

~~~text
taxi_api_requests_total
~~~

Lalu coba:

~~~text
sum(rate(taxi_api_requests_total[1m]))
~~~

Jangan cuma copy query.

Coba jelaskan bedanya:

~~~text
first query
→ cumulative request count

second query
ₒ recent request rate
~~~

Kalau logik itu paham, belajar PromQL berikutnya jauh lebih mudah.

---

# Target Status

Prometheus punya target page.

Kalau API target:

~~~text
DOWN
~~~

jangan debug Grafana dulu.

Debug chain:

~~~text
FastAPI hidup?
ₒ
/metrics bisa diakses?
ₒ
Prometheus network benar?
ₒ
target hostname benar?
ₒ
scrape berhasil?
~~~

Grafana cuma bisa visualisasi data yang sudah masuk Prometheus.

---

# Metric naming

Metric name sebaiknya menjelaskan semantics dan unit.

Contoh:

~~~text
taxi_api_request_duration_seconds
~~~

langsung jelas unit-nya second.

Suffix seperti:

~~~text
_total
_seconds
_info
~~~

membantu konsistency.

Bad:

~~~text
model_metric
~~~

Good:

~~~text
taxi_model_recent_mae
~~~

Nama yang jelas sangat membantu ketika metric sudah banyak.

---

# Prometheus bukan alert magic

Punya metric belum berarti kita otomatis tahu threshold yang benar.

Misalnya p95 latency 0.8 second.

Apakah buruk?

Tergantung SLO aplikasi.

Monitoring tool memberi observability, tapi interpretation tetap perlu domain context.

Hal yang sama berlaku buat MAE.

---

# Checkpoint

Coba jawab:

1. Apa itu scrape?
2. Pull model maksudnya apa?
3. Counter, Gauge, Histogram beda apa?
4. Counter vs rate analoginya apa?
5. Kenapa p95 useful?
6. Apa itu cardinality?
7. Kenapa request_id buruk jadi label?
8. Kenapa detailed prediction lebih cocok jadi log daripada metric?
9. Kalau Grafana kosong, kenapa Prometheus target perlu dicek dulu?
10. Kenapa metric tetap butuh domain interpretation?
