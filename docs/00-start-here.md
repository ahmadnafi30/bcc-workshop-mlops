# MLOps Workshop: Mulai dari Sini 👋

Selamat datang! Di workshop ini kita akan mengubah satu model taxi sederhana menjadi sistem yang bisa **dilatih, dilacak, dijalankan lewat API, dan dipantau**. Kamu tidak perlu hafal semua nama tools dulu — kita belajar dari cerita dan problem-nya.

[Mulai tur tools](#kenalan-dengan-ui-klik-apa-dan-lihat-apa){ .md-button .md-button--primary }
[Buka quickstart dashboard](10-hands-on/dashboard-quickstart.md){ .md-button }

!!! tip "Baru pertama kali belajar MLOps?"
    Baca halaman ini dulu selama beberapa menit. Setelah itu pilih **Quickstart Grafana** untuk demo end-to-end, atau ikuti **Hands-on Workshop** berurutan kalau sedang ikut sesi kelas.

## Cerita kita: bantu tim taxi bersiap untuk jam berikutnya 🚕

Bayangkan sebuah tim operasi ingin tahu berapa banyak taxi yang akan dibutuhkan di tiap zona Manhattan satu jam ke depan. Data perjalanan baru datang, jadi kita perlu menyiapkannya, membuat prediksi, lalu memeriksa apakah sistem dan model masih bekerja dengan baik.

Contoh sederhananya:

| Pertanyaan | Contoh |
| --- | --- |
| Apa yang diprediksi? | Jumlah pickup taxi per zona pada jam berikutnya |
| Model belajar dari apa? | Riwayat pickup pada waktu dan zona sebelumnya |
| Bagaimana aplikasi memakai model? | Mengirim request ke prediction API |
| Bagaimana kita tahu hasilnya? | Membandingkan prediksi dengan actual setelah data aktual tersedia |

Jadi goal workshop ini bukan cuma membuat satu file model. Kita belajar **bagaimana model hidup sebagai bagian dari sebuah layanan**.

## Peta perjalanan — satu tool, satu pekerjaan

Urutannya bisa dibaca seperti perjalanan data ini:

~~~text
Data taxi
   ↓ siapkan dan catat snapshot (DVC)
Airflow mengatur urutan workflow
   ├── training → MLflow Tracking (catat dan bandingkan runs)
   │                    ↓
   │               Model Registry (pilih champion)
   │                    ↓
   │               FastAPI (layani predictions)
   │                    ↓
   │               Prometheus → Grafana (pantau service)
   └── actual + predictions → evaluasi kualitas model
                                      ↓ jika perlu
                                  retraining run baru
~~~

| Tool | Pertanyaan yang dijawab | Contoh yang bisa kamu lakukan |
| --- | --- | --- |
| **DVC** | Dataset/snapshot mana yang dipakai? | Reproduksi snapshot training yang sama |
| **MLflow Tracking** | Training run mana yang hasilnya lebih baik? | Lihat parameters, metrics, dan artifacts |
| **MLflow Model Registry** | Model version mana yang dipilih untuk serving? | Review candidate, lalu gunakan alias champion |
| **Airflow** | Pekerjaan apa yang dijalankan, kapan, dan setelah apa? | Trigger DAG dan buka log task yang gagal |
| **FastAPI** | Bagaimana aplikasi meminta prediksi? | Cek health dan coba endpoint API |
| **Prometheus** | Apa yang sedang terjadi pada service? | Cek target dan query metrics |
| **Grafana** | Bagaimana membaca keadaan sistem sekilas? | Lihat traffic, latency, dan hasil evaluasi |

!!! info "DVC dan MLflow bukan duplikat"
    **DVC** membantu mengelola versi file data dan pipeline. **MLflow** mencatat eksperimen model serta model versions. Cara gampangnya: DVC menjawab “data yang mana?”, MLflow menjawab “run/model yang mana dan hasilnya bagaimana?”.

## Sebelum membuka dashboard

Jalankan workshop dari root repository dengan Docker yang aktif. Quickstart lengkap ada di [Mengisi Dashboard Grafana](10-hands-on/dashboard-quickstart.md); panduan setup ada di [Step 0 — Setup](10-hands-on/setup.md).

Untuk Windows, ikuti panduan di WSL2 bila menggunakan command Bash pada quickstart. Docker Desktop harus aktif. Pada Linux/macOS, gunakan terminal biasa. Sebelum mengikuti langkah praktis, cek dulu bahwa halaman service bisa dibuka:

| Buka halaman | Artinya | Yang diharapkan |
| --- | --- | --- |
| [MLflow](http://localhost:5000) | Tempat melihat training dan model | UI terbuka; daftar run terisi setelah training |
| [Airflow](http://localhost:8080) | Tempat mengatur workflow | Halaman login, lalu DAG workshop |
| [API health](http://localhost:8000/health) | Cek API hidup | Status health menunjukkan service aktif |
| [API Swagger](http://localhost:8000/docs) | Coba endpoint API | Daftar endpoint muncul |
| [Prometheus targets](http://localhost:9090/targets) | Cek apakah metric berhasil di-scrape | Target taxi-api berstatus UP |
| [Grafana dashboard](http://localhost:3000/d/taxi-demand-mlops/taxi-demand-mlops) | Ringkasan service dan model | Dashboard Taxi Demand MLOps terbuka |

Local Grafana memakai user/password default `admin`/`admin` kecuali nilainya diganti di file `.env`. Airflow standalone membuat credential lokal saat pertama dijalankan; ikuti petunjuk di [modul workshop](workshop-module.md).

!!! warning "Halaman terbuka belum berarti semua datanya sudah ada"
    Aplikasi bisa hidup walaupun belum ada dataset, model, prediction traffic, atau hasil evaluasi. Isi dashboard muncul setelah langkah yang menghasilkan data dijalankan. Itu biasanya bukan error; cek tahap mana yang belum dikerjakan di tabel berikut.

| Yang kamu lihat | Apa artinya | Bagaimana membuat isinya |
| --- | --- | --- |
| MLflow terbuka tetapi experiment belum punya runs | Tracking server hidup, belum ada training yang dicatat | Jalankan [training dengan MLflow](06-experiment-tracking/experiment-tracking.md) |
| DAG Airflow tampil tetapi belum ada run | Airflow sudah membaca workflow, belum ada workflow yang di-trigger | Trigger DAG setelah data/dependency siap |
| API health sehat tetapi model-info belum tersedia | API hidup, belum ada alias model champion yang bisa dilayani | Train, register, lalu promote model sesuai quickstart |
| Target Prometheus UP tetapi panel prediction kosong | Metrics berhasil diambil, belum ada request prediction | Kirim traffic memakai script pada quickstart |
| Dashboard Grafana terbuka tetapi MAE belum ada | Belum ada prediksi yang cocok dengan actual dan dihitung evaluator | Jalankan prediction, lalu evaluasi setelah data actual tersedia |

## Kenalan dengan UI: klik apa dan lihat apa

### 1. MLflow Tracking — cari tahu run mana yang lebih bagus 🧪 {#mlflow-ui}

Buka [MLflow](http://localhost:5000), lalu:

1. Pilih experiment **taxi-demand-forecasting**.
2. Cari run seperti **naive-24h** dan **hist-gradient-boosting**. Nama run dapat bertambah atau berbeda setelah retraining.
3. Bandingkan kolom **MAE** dan **RMSE**. Untuk MAE, angka yang lebih kecil berarti rata-rata kesalahan lebih rendah.
4. Klik salah satu run untuk membaca **Parameters**, **Metrics**, **Tags**, dan **Artifacts**.
5. Cari informasi snapshot/dataset untuk mengetahui data yang dipakai. Buka artifacts untuk melihat output model atau report yang dicatat oleh run.

Kalau run belum ada, jalankan training dahulu — jangan menilai MLflow error hanya dari tabel yang masih kosong. Lanjut ke [tur MLflow Tracking](06-experiment-tracking/experiment-tracking.md) dan [Step 4 — MLflow](10-hands-on/step-04-mlflow.md).

!!! question "Apa bedanya MAE dan RMSE?"
    Dua-duanya mengukur error prediksi. MAE lebih mudah dibaca sebagai rata-rata besar selisih. RMSE memberi penalti lebih besar pada error yang sangat besar. Di workshop, bandingkan model pada dataset/evaluation yang sama.

### 2. Model Registry — lihat model yang siap dipakai 🚦 {#registry-ui}

Di MLflow, buka menu **Models** atau halaman registry, lalu pilih **taxi-demand-forecasting-model**.

- **Version** adalah rekaman model yang terdaftar. Versi baru tidak menimpa versi lama.
- **Source run** memberi tahu run mana yang membuat model itu.
- Alias **challenger** menandai candidate untuk ditinjau.
- Alias **champion** menunjukkan versi yang dipakai API sebagai model aktif.

Satu run bagus belum otomatis menjadi champion. Ikuti proses register/review/promotion di [Model Registry](06-experiment-tracking/model-registry.md). Untuk melihat model yang benar-benar dibaca API, cek [model-info](http://localhost:8000/model-info) dan bandingkan dengan panel **Serving Model (Last Prediction)** di Grafana.

### 3. Airflow — lihat workflow berjalan per task 🛠️ {#airflow-ui}

Buka [Airflow](http://localhost:8080), login memakai credential lokal, lalu cari tiga DAG berikut:

| DAG | Gunanya | Sebelum di-trigger |
| --- | --- | --- |
| **taxi_daily_replay** | Menyiapkan satu hari data historical dan membangun ulang features | Data replay untuk tanggal itu harus tersedia |
| **taxi_initial_training** | Membuat snapshot, mencatat training runs, dan mendaftarkan candidate jika lolos gate | Data dan dependency training harus siap |
| **taxi_model_monitoring** | Mengevaluasi champion dan menjalankan retraining bila memenuhi kondisi | Prediction log dan actual demand harus tersedia |

Semua DAG workshop memakai **manual trigger**. Artinya, melihat DAG pada daftar tidak otomatis menjalankan proses.

Untuk belajar membaca Airflow, pilih satu DAG, buka tampilan **Grid** atau **Graph**, lalu ikuti urutannya:

1. Setiap kotak adalah task; garis menunjukkan dependency.
2. Setelah run selesai, task hijau berarti sukses. Task merah berarti buka task itu lalu **Logs** untuk menemukan penyebab.
3. Klik **Trigger** hanya saat input untuk DAG tersebut siap.
4. Pada daily replay, parameter `replay_date` berformat tanggal, contoh `2025-01-27`.
5. Monitoring bisa membuat retraining candidate saat hasil evaluasi memenuhi threshold. Jalankan setelah prediction dan actual siap, lalu baca hasilnya sebelum melakukan promotion.

Kalau task gagal, catat **nama DAG, run, task, dan pesan log**. Itu lebih membantu daripada hanya mengatakan “Airflow error”. Baca [tur konsep Airflow](03-tools/airflow.md) atau [Step 5 — Airflow](10-hands-on/step-05-airflow.md).

### 4. FastAPI — coba pintu masuk prediction 📮

Buka [Swagger UI](http://localhost:8000/docs).

- `GET /health`: memastikan API merespons. Ini belum membuktikan bahwa model sudah siap.
- `GET /model-info`: melihat model version/alias yang sedang tersedia. Jika model belum dipromosikan, layanan bisa belum memberi informasi model.
- `POST /predict`: mengirim features/history untuk memperoleh prediction. Contoh request ada di [Step 6 — FastAPI](10-hands-on/step-06-api.md).

Swagger membantu mencoba API dari browser tanpa menulis client terlebih dahulu. Baca status response dan body-nya; kode 4xx biasanya berarti input belum sesuai, sedangkan 5xx perlu dicek di log service.

### 5. Prometheus — pastikan metric berhasil dikumpulkan 📈

Buka [Prometheus Targets](http://localhost:9090/targets). Target **taxi-api** yang berstatus **UP** berarti Prometheus berhasil mengambil metrics dari API.

Lalu buka halaman [Prometheus](http://localhost:9090), ketik query `up`, dan pilih **Execute**. Nilai `1` berarti target hidup saat scrape; `0` berarti target sedang tidak bisa dijangkau. Prometheus mengukur service, sedangkan evaluasi MAE berasal dari proses evaluation yang berbeda.

### 6. Grafana — baca keadaan layanan dalam satu layar 📊 {#grafana-ui}

Buka [dashboard Taxi Demand MLOps](http://localhost:3000/d/taxi-demand-mlops/taxi-demand-mlops). Pilih rentang waktu **Last 30 minutes** untuk melihat traffic demo terbaru.

- **Prediction Request Rate**, **Prediction Latency**, dan **Predictions in 5m**: request yang benar-benar melewati endpoint prediction.
- **Serving Model (Last Prediction)**: versi yang menghasilkan prediksi terakhir.
- **Model MAE**, **Evaluation Samples**, dan **Model Evaluation Status**: kualitas model setelah prediksi dicocokkan dengan actual.
- **Evaluated Model**: identitas model yang menjadi sumber hasil evaluasi.

Panel-panel ini punya sumber data dan timing berbeda. Misalnya traffic bisa sudah terlihat sementara MAE masih **Belum dievaluasi**. Gunakan urutan lengkap pada [Quickstart Grafana](10-hands-on/dashboard-quickstart.md): siapkan taxi data → training/register → kirim prediction traffic → evaluate → refresh dashboard.

## Jalur belajar yang disarankan

Pilih jalur yang cocok. Kamu tidak perlu membaca semua reference sekaligus.

=== "Saya ingin memahami konsep dulu"

    1. [Workshop Overview](01-introduction/workshop-overview.md)
    2. [MLOps from Zero](01-introduction/mlops-from-zero.md)
    3. [Architecture](01-introduction/architecture.md)
    4. [Use case dan dataset](02-use-case/problem-statement.md)

=== "Saya ingin dashboard berisi"

    1. [Quickstart Grafana](10-hands-on/dashboard-quickstart.md)
    2. [Troubleshooting](10-hands-on/troubleshooting.md)
    3. Setelah paham demo, pelajari [monitoring concepts](09-monitoring/monitoring-concepts.md)

=== "Saya sedang ikut workshop"

    Ikuti [Hands-on Step 0 sampai Step 10](10-hands-on/setup.md) secara berurutan. [Modul Workshop](workshop-module.md) adalah panduan lengkap untuk agenda dan fasilitator, jadi tidak harus menjadi bacaan pertama.

=== "Saya butuh jawaban satu topik"

    Buka halaman [MLflow](06-experiment-tracking/experiment-tracking.md), [Airflow](03-tools/airflow.md), [Grafana](09-monitoring/grafana.md), atau [Glossary](glossary.md). Tiap halaman mendalami satu bagian dan bisa dibaca sebagai reference.

## Kalau ada yang belum beres

Coba cek dari lapisan yang paling mudah:

1. Apakah Docker Engine sudah aktif dan containers berstatus sehat?
2. Apakah service bisa dibuka dari browser?
3. Apakah input yang dibutuhkan (taxi data, model champion, prediction) sudah dibuat?
4. Jika Airflow task merah, baca log task itu. Jika endpoint error, baca response dan API logs.
5. Gunakan tabel di [Troubleshooting](10-hands-on/troubleshooting.md) sebelum mengulang seluruh workshop.

!!! success "Satu checkpoint untuk pemula"
    Kalau kamu bisa menjelaskan **data masuk → model dilatih dan dicatat → model disajikan sebagai API → service dan kualitasnya dipantau**, kamu sudah memahami bentuk besar MLOps. Detail tools-nya bisa dipelajari selangkah demi selangkah. 🎉