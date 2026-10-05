# Grafana — Dari Metric Mentah Jadi Dashboard yang Bisa Dibaca Manusia

Prometheus punya data.

Tapi kalau setiap kali mau inspect system kita harus ngetik query satu-satu, kurang nyaman.

Grafana jadi visualization layer.

Mental model:

~~~text
Prometheus
→ collect + query

Grafana
→ visualize + dashboard
~~~

---

## Datasource

Grafana perlu tahu data source.

Project provision:

~~~text
Prometheus
http://prometheus:9090
~~~

Di Compose network, hostname prometheus resolve ke Prometheus container.

---

## Provisioning

Dashboard kita tidak dibuat manual lalu cuma hidup di laptop presenter.

Config disimpan di repo.

~~~text
monitoring/grafana/
├── provisioning/
└── dashboards/
~~~

Benefit:

~~~text
git clone
↓
docker compose up
↓
same dashboard
~~~

Dashboard jadi code/config artifact.

Bisa versioned dan reviewed.

---

## Panel utama

Dashboard menampilkan:

- request rate dan p50/p95 latency khusus `/predict`,
- jumlah prediction berhasil dalam 5 menit,
- persentase response 4xx dan 5xx dari `/predict`,
- status evaluasi model,
- recent MAE, reference MAE, dan threshold retraining,
- jumlah prediction yang sudah cocok dengan actual dan minimum sample,
- waktu job evaluasi terakhir, umur evaluasi, dan target replay terakhir,
- versi model dari prediction API terakhir dan versi model yang dievaluasi.

Setiap panel punya description. Hover ikon info untuk membaca arti angka dan
window yang dipakai.

Request rate memakai window 1 menit, sedangkan latency dan error rate memakai
window 5 menit. `/metrics`, `/health`, dan Swagger tetap dicatat oleh middleware,
tetapi tidak ikut masuk panel prediction. Jadi scrape Prometheus tidak terlihat
seolah-olah ada user yang meminta prediksi.

4xx berarti request ditolak, misalnya target bukan awal jam atau history belum
lengkap. 5xx berarti layanan gagal menangani request. Periksa response untuk
mengetahui penyebabnya; kedua jenis error perlu dibaca dengan konteks berbeda.

Kenapa combine operational + model metric?

Supaya satu view bisa bantu differentiate:

~~~text
service problem
vs
model problem
~~~

---

## Status model perlu evidence

MAE nol berarti prediction cocok dengan actual. Kalau belum ada actual yang
bisa dievaluate, kualitas model belum diketahui. Dashboard menampilkan N/A
untuk MAE tersebut.

| Status | Artinya |
| --- | --- |
| Belum dievaluasi | Belum ada prediction yang cocok dengan actual, atau summary belum tersedia. |
| Sampel belum cukup | Sudah ada MAE, tetapi sample masih di bawah minimum. |
| Dalam batas | Sample cukup dan MAE tidak melewati threshold. |
| Perlu retrain | Sample cukup dan MAE melewati threshold. |

Grafik **Model MAE** menampilkan threshold yang dihitung oleh job evaluasi:

~~~text
threshold = reference MAE × degradation multiplier
~~~

Dengan default multiplier 1.25, reference MAE 10 menghasilkan threshold 12.5.
Tetap lihat **Evaluation Samples** sebelum mengambil keputusan.

---

## Dua clock dalam historical replay

**Last Evaluation** dan **Evaluation Age** mengikuti waktu nyata ketika job
dijalankan. Scrape setiap 5 detik tidak berarti job evaluasi ikut berjalan
setiap 5 detik.

**Latest Evaluated Replay Target** mengikuti tanggal historical dari prediction
yang sudah cocok dengan actual. Tanggal 2025 tetap normal walaupun workshop
dilakukan sekarang. Panel ini bukan ukuran freshness job.

Dashboard memakai timezone `America/New_York`. Summary menyimpan waktu job dalam
UTC dan target replay sebagai waktu lokal NYC; exporter mengubah keduanya ke
timestamp yang sesuai sebelum ditampilkan.

---

## Sesudah model dipromote

**Serving Model (Last Prediction)** menunjukkan model dari prediction API
terakhir. Kirim prediction baru sesudah promotion untuk melihat pergantian versi.

**Evaluated Model** menunjukkan model sumber summary evaluasi. Jika serving
sudah v2 tetapi evaluation masih v1, MAE yang terlihat masih milik v1. Jalankan
evaluasi lagi untuk model baru dan tunggu actual dari prediction model tersebut.

Loader resolve alias champion lalu memuat artifact lewat URI versi tetap.
Metadata dan model yang digunakan tetap cocok walaupun alias berubah saat
artifact sedang dimuat.

---

## Dashboard empty bukan berarti broken

Kalau belum ada traffic:

~~~text
request rate = no data / zero
~~~

Normal. Error rate dan latency juga bisa belum tersedia saat tidak ada traffic.
Jangan menganggap panel kosong sebagai zero latency atau zero error yang sudah
terbukti. Prometheus perlu lebih dari satu scrape untuk menghitung rate.

Generate actual API traffic:

~~~bash
uv run python scripts/generate_api_traffic.py   --date 2025-01-28   --start-hour 17   --end-hour 18
~~~

Kenapa script ini lewat HTTP?

Supaya middleware metrics beneran triggered.

Direct predictor replay nggak create HTTP latency metric.

---

## Data chain

Kalau recent MAE panel kosong, debug chain:

~~~text
prediction happened?
↓
prediction log written?
↓
ground truth exists?
↓
evaluate_predictions ran?
↓
performance_summary exists?
↓
/metrics exposes gauge?
↓
Prometheus scraped?
↓
Grafana query correct?
~~~

Observability debugging juga perlu dependency thinking.

---

## Dashboard bukan source of truth sendiri

Grafana visualize.

Dia bukan tempat business logic retrain.

Decision summary dihasilkan monitoring pipeline.

Prometheus scrape metric.

Grafana visualize.

Separation:

~~~text
logic
→ monitoring code

metrics storage
→ Prometheus

visualization
→ Grafana
~~~

---

## Alerting?

Grafana/Prometheus ecosystem bisa alert.

Workshop belum fokus ke alert channel.

Future extension:

~~~text
retrain_recommended = 1
↓
alert
↓
Slack/email/on-call
~~~

Tapi jangan buru-buru add alert sebelum metric quality jelas.

---

## Checkpoint

1. Grafana beda apa dengan Prometheus?
2. Provisioning dashboard benefit-nya apa?
3. Kenapa dashboard bisa kosong padahal Grafana sehat?
4. Kalau MAE panel kosong, dependency chain apa yang dicek?
5. Kenapa retraining logic nggak ditaruh di Grafana?
