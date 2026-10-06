# Modul Workshop: Bringing Machine Learning into Production

**Studi kasus:** prediksi jumlah pickup NYC Yellow Taxi per Manhattan taxi zone,
satu jam ke depan.

**Repository:** `bcc-workshop-mlops`

**Fasilitator:** Ahmad Nafi Mubarok dan Fatoni Murfid Syafii

**Peserta:** sudah mengenal Python, Pandas, regression, train/validation split,
dan Git dasar; belum perlu pengalaman MLOps.

**Durasi rancangan:** 6 jam termasuk 25 menit jeda, dengan persiapan environment
dan download data dilakukan sebelum kelas. Bisa dibagi menjadi dua pertemuan.

Modul ini menjadi pegangan utama untuk konsep, praktik, dan evaluasi workshop.
Command mengikuti script dan konfigurasi repo. Untuk langsung mengisi dashboard,
gunakan [panduan Grafana dari kondisi kosong](10-hands-on/dashboard-quickstart.md).

## 1. Tujuan pembelajaran

Setelah workshop, peserta dapat:

1. Menjelaskan hubungan data, feature, model artifact, API, dan monitoring.
2. Menyiapkan dataset temporal tanpa memakai informasi target sebagai feature.
3. Membandingkan model dengan baseline pada periode validation yang sama.
4. Menelusuri model production ke MLflow run dan fingerprint dataset.
5. Membuat prediction melalui API dengan metadata versi yang jelas.
6. Membaca kesehatan service dan kualitas model sebagai dua jenis sinyal.
7. Menjelaskan kapan retraining layak dilakukan dan mengapa promotion perlu review.
8. Membaca workflow Airflow serta membedakan delivery kode dengan lifecycle model.

Hasil akhir praktik adalah champion yang dapat diserve melalui HTTP, dashboard
dengan traffic nyata, dan evaluasi yang mempunyai ground truth serta identitas
model. Peserta juga menyerahkan bukti lineage dan rekomendasi tindakan dari
dashboard.

## 2. Persiapan dan agenda

### Persiapan sebelum kelas

- Install Git, uv, dan Docker dengan Compose; aktifkan Docker Engine/Desktop.
- Gunakan Bash di Linux, macOS, atau WSL2 untuk command dalam modul.
- Clone repo, jalankan `uv sync`, doctor, dan pytest.
- Download data Januari melalui `scripts/bootstrap_data.py --months 2025-01`.
- Siapkan image stack lewat langkah 2 pada panduan Grafana.
- Pastikan port 3000, 5000, 8000, 8080, dan 9090 tersedia sesuai sesi yang digunakan.
- Sediakan disk untuk data, environment, dan image serta memori untuk membaca
  Parquet bulanan. Airflow menambah kebutuhan resource; fasilitator dapat
  mendemokan sesi ini jika laptop peserta terbatas.

Download dan build pertama tidak termasuk waktu latihan. Bila belum selesai,
fasilitator menyediakan waktu persiapan tambahan sebelum membuka kelas.

### Agenda kelas

| Sesi | Materi dan aktivitas | Menit | Bukti hasil |
| --- | --- | ---: | --- |
| 1 | Masalah production ML dan peta sistem | 15 | Peserta memetakan kebutuhan ke komponen |
| 2 | Environment, struktur repo, dan service | 25 | Doctor, tests, dan service siap |
| 3 | Data, replay, feature, dan leakage | 45 | Hourly demand dan feature dataset |
| 4 | Baseline, training, dan MLflow | 45 | Dua run yang dapat dibandingkan |
| 5 | DVC, lineage, registry, dan promotion | 40 | Snapshot dan champion tercatat |
| 6 | Serving melalui FastAPI dan Docker | 30 | Prediction HTTP 200 dengan metadata |
| 7 | Prometheus, Grafana, dan evaluasi model | 55 | Traffic, MAE, dan status evaluasi |
| 8 | Airflow dan feedback loop retraining | 45 | DAG run dan keputusan tindakan |
| 9 | CI/CD dan latihan membaca workflow | 25 | Pemetaan checks dan delivery |
| 10 | Presentasi hasil dan evaluasi | 10 | Laporan peserta |
| — | Jeda, dibagi sesuai kebutuhan kelas | 25 | — |
| **Total** | | **360** | |

Gunakan pola **konsep → demonstrasi → praktik → pemeriksaan bukti → diskusi**.
Peserta berpasangan dapat bergantian menjadi operator terminal dan pemeriksa
hasil. Jika kelas dibagi dua, akhiri pertemuan pertama setelah champion tersedia;
mulai pertemuan kedua dari prediction API dan monitoring.

## 3. Sesi 1 — Dari model menjadi sistem

### Masalah yang ingin diselesaikan

Model dengan validation MAE yang baik belum menjawab pertanyaan operasional:
dataset mana yang dipakai, bagaimana backend memanggil model, versi apa yang
sedang melayani request, dan siapa yang mengetahui kualitasnya menurun.

Dalam repo ini, forecast dapat membantu memahami kebutuhan armada per area.
Targetnya adalah jumlah pickup pada satu zone dan satu jam. Angka prediksi dapat
berupa desimal karena model regression menghasilkan estimasi jumlah pickup.

### Peta alur repo

```text
TLC monthly Parquet + zone lookup
  → Manhattan replay source
  → hourly demand per zone
  → lag/calendar/rolling features
  → training snapshot + DVC
  → baseline dan HGB → MLflow runs → Registry champion
  → FastAPI /predict → prediction log
  → match actual demand → performance summary
  → Prometheus scrape → Grafana
  → keputusan retraining → challenger → review → champion
```

Airflow mengoordinasikan sebagian pekerjaan batch. Docker menyediakan runtime
service. GitHub Actions memeriksa kode dan membangun/menerbitkan image.

| Pertanyaan | Komponen repo | Tanggung jawab |
| --- | --- | --- |
| Data apa yang dipakai model? | Snapshot, DVC, SHA256 | Identitas input training |
| Parameter dan metric run mana? | MLflow Tracking | Catatan experiment dan artifact |
| Model mana yang diserve? | Model Registry | Version serta alias champion/challenger |
| Bagaimana pekerjaan batch dijalankan? | Airflow | Dependency task, state, dan log |
| Bagaimana aplikasi meminta forecast? | FastAPI | Kontrak request dan response |
| Bagaimana runtime dikemas? | Docker Compose | Image dan hubungan service lokal |
| Bagaimana perubahan kode diperiksa? | GitHub Actions | Lint, tests, docs, dan build |
| Apakah service dan model sehat? | Prometheus + Grafana + evaluasi | Sinyal operasional dan kualitas |

**Diskusi:** pilih tiga pertanyaan di atas. Jelaskan artifact yang harus tersedia
agar pertanyaan tersebut dapat dijawab dengan bukti.

## 4. Sesi 2 — Environment dan struktur repo

### Praktik 2A: jalankan pemeriksaan awal

Semua command berikut dijalankan dari root repo pada terminal host:

```bash
uv sync
uv run python --version
uv run python scripts/doctor.py
uv run pytest -q
```

Project menggunakan Python 3.11. `uv sync` memasang dependency project; `uv run`
menjalankan command di environment project. Airflow dan MkDocs mempunyai
dependency group terpisah.

| Lokasi | Fungsi | Contoh yang dibaca |
| --- | --- | --- |
| `src/` | Logic reusable | `src/features/build_features.py` |
| `scripts/` | Entry point manual | `scripts/train_with_mlflow.py` |
| `dags/` | Definisi workflow batch | `dags/taxi_daily_replay.py` |
| `api/` | HTTP layer dan schema | `api/main.py`, `api/schemas.py` |
| `tests/` | Pemeriksaan perilaku | `tests/test_serving_features.py` |
| `monitoring/` | Config scrape dan dashboard | `monitoring/grafana/dashboards/taxi-mlops.json` |

### Praktik 2B: siapkan service inti

```bash
mkdir -p .mlflow/artifacts data
docker info
docker compose up -d --build grafana
docker compose ps
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
```

Grafana mempunyai dependency Prometheus, yang bergantung pada API dan MLflow.
Airflow akan dinyalakan pada sesi 8. Gunakan server MLflow Docker ini untuk semua
script host; environment di container memakai hostname service `mlflow`.

| Alamat default | Kegunaan |
| --- | --- |
| <http://localhost:5000> | Tracking dan model registry |
| <http://localhost:8000/docs> | Swagger untuk prediction API |
| <http://localhost:9090> | Prometheus dan status target |
| <http://localhost:3000/d/taxi-demand-mlops/taxi-demand-mlops> | Grafana dashboard |

**Checkpoint:** API `/health` menjawab `ok`. Sebelum champion tersedia,
`/model-info` dapat menjawab 503. Ini menunjukkan bahwa health endpoint saat ini
menguji proses API, sedangkan kesiapan inference memerlukan model dan data.

Jika ingin membaca docs sambil menjalankan API, gunakan port berbeda:

```bash
uv sync --group docs
uv run --group docs mkdocs serve --dev-addr 127.0.0.1:8002
```

**Pertanyaan:** mengapa adanya Docker CLI belum membuktikan daemon aktif?
Mengapa tests awal dibutuhkan sebelum mulai mengubah feature?

## 5. Sesi 3 — Data temporal, feature, dan leakage

### Data dan waktu replay

Bootstrap mengambil Yellow Taxi monthly Parquet, memfilter pickup Manhattan,
dan menyimpan replay source. Demand harian disimpan sebagai grid semua zone
Manhattan × 24 jam. Kombinasi tanpa pickup diisi nol agar satu row tetap mewakili
satu jam.

Workshop menjalankan data historical sebagai replay. Timestamp request API
harus tanpa timezone dan dianggap sebagai waktu lokal NYC. Waktu sistem saat
script berjalan berbeda dari tanggal historical yang diprediksi.

| Periode initial | Peran |
| --- | --- |
| Jan 1–7, 2025 | Warm-up untuk lag 168 jam |
| Jan 8–21 | Training model |
| Jan 22–26 | Validation initial |
| Jan 27–28 | History lanjutan dan replay inference/evaluasi |

### Praktik 3A: siapkan hourly demand dan feature

```bash
uv run python scripts/bootstrap_data.py --months 2025-01
uv run python scripts/prepare_historical_demand.py \
  --start-date 2025-01-01 --end-date 2025-01-28
uv run python scripts/build_features.py \
  --start-date 2025-01-01 --end-date 2025-01-26 --force
```

Jika bootstrap sudah dikerjakan sebelum kelas, file existing dapat dilewati
tanpa download ulang. Jangan memakai `--force` pada bootstrap hanya untuk
mengulang latihan.

| Kelompok feature | Kolom | Intuisi |
| --- | --- | --- |
| Identitas | `zone_id` | Pola berbeda per area; categorical |
| Kalender | `hour`, `day_of_week`, `is_weekend` | Pola jam dan hari |
| Lag | `lag_1h`, `lag_2h`, `lag_3h`, `lag_24h`, `lag_168h` | Demand pada jam sebelumnya |
| Rolling | `rolling_mean_3h`, `rolling_mean_6h`, `rolling_mean_24h` | Rata-rata demand sebelum target |

### Praktik 3B: baca kontrak feature

Buka `src/features/build_features.py` dan
`src/serving/feature_provider.py`. Untuk target Jan 28 pukul 18:00:

- `lag_1h` berasal dari pukul 17:00 pada hari yang sama.
- `lag_24h` berasal dari Jan 27 pukul 18:00.
- `lag_168h` berasal dari Jan 21 pukul 18:00.
- Rolling 3 jam memakai pukul 15:00, 16:00, dan 17:00.
- Actual pukul 18:00 dipakai sebagai target/evaluasi, bukan feature history.

Pada offline feature, rolling didahului `shift(1)` dan dihitung per zone.
Shift baris mewakili jam hanya ketika grid per zone lengkap dan berurutan.
Pada serving, provider membangun index lookback 168 jam dan menolak history
yang bolong.

**Latihan:** tuliskan tiga cara leakage dapat terjadi: memasukkan actual target
ke rolling, memasukkan tanggal replay ke snapshot initial, dan membandingkan
model dengan split yang memakai informasi masa depan. Jelaskan pencegahannya.

**Bukti hasil:** feature mulai setelah warm-up dan berakhir Jan 26; file demand
Jan 28 tetap tersedia di folder processed untuk serving dan evaluasi.

## 6. Sesi 4 — Baseline, training, dan experiment tracking

### Konsep inti

Baseline naive 24 jam memakai demand pada jam yang sama sehari sebelumnya.
HGB menggunakan seluruh feature tabular. Keduanya dievaluasi pada snapshot dan
validation window yang sama sehingga perbandingan awalnya adil.

MAE adalah rata-rata absolute error, dalam satuan pickup. RMSE lebih memberi
bobot pada error besar. Misalnya actual `[10, 10, 10]` dan prediksi
`[10, 11, 12]` menghasilkan MAE 1. Nilai rendah perlu dilihat bersama periode,
jumlah sample, dan baseline pembanding.

### Praktik 4A: buat snapshot dan train

```bash
uv run python scripts/create_training_snapshot.py --cutoff-date 2025-01-26
uv run python scripts/train_with_mlflow.py
```

Script membuat run baseline dan model. Model artifact HGB disimpan dengan format
`skops` dan trusted types yang didefinisikan di repo. Simpan run ID dari baris
`model`, bukan baseline yang tidak mempunyai artifact sklearn model.

### Praktik 4B: baca MLflow UI

Buka experiment `taxi-demand-forecasting` pada <http://localhost:5000>.
Catat informasi berikut dalam laporan:

| Informasi | Yang dicari |
| --- | --- |
| Run identity | Run ID baseline dan model |
| Model parameter | Learning rate, max iteration, random state |
| Dataset identity | Snapshot name, SHA256, jumlah row dan zone |
| Dataset period | Tanggal awal/akhir snapshot dan ukuran split |
| Metrics | MAE dan RMSE masing-masing run |
| Artifact | Model, input example, dan signature pada model run |

**Checkpoint:** jelaskan mengapa nama `final.parquet` saja belum cukup untuk
mengetahui input experiment. Hash menggambarkan isi file snapshot yang benar-benar
dipakai; versi kode dan dependency tetap diperlukan untuk reproduksi lengkap.

**Diskusi:** jika HGB kalah dari naive 24 jam, keputusan yang baik adalah
menyelidiki model dan data sebelum promotion. Kemampuan menjalankan training
tidak otomatis menjadi alasan menjadikan model tersebut champion.

## 7. Sesi 5 — DVC, lineage, dan model registry

### Praktik 5A: kelola snapshot melalui DVC

Baca stage `create_training_snapshot` dalam `dvc.yaml`: `cmd` mendefinisikan
pekerjaan, `deps` input yang memengaruhinya, dan `outs` hasil yang dikelola.
Jalankan pada host di Git checkout repo:

```bash
uv run dvc repro create_training_snapshot
uv run dvc status
uv run dvc repro create_training_snapshot
```

Repro pertama dapat mengeksekusi stage dan membuat state pipeline. Repro kedua
dapat melewati stage bila dependency/output sudah selaras. Catat status yang
benar-benar muncul. Repo belum mendefinisikan DVC remote bersama; cache lokal
saja belum menjadi mekanisme pertukaran data antar laptop.

Jika DVC membangun ulang snapshot setelah run sesi 4, ulangi training untuk
laporan akhir agar fingerprint model menunjuk snapshot hasil DVC yang sekarang:

```bash
uv run python scripts/train_with_mlflow.py
```

### Praktik 5B: register dan promote

Ganti placeholder berikut dengan run ID model yang dipilih:

```bash
uv run python scripts/register_model.py --run-id "RUN_ID_MODEL"
```

Catat version hasil registration. Alias `challenger` menunjukkan candidate.
Setelah membaca metric dan lineage, promote version yang dipilih:

```bash
uv run python scripts/promote_model.py --version "VERSI_MODEL"
```

Registration manual tidak memasang gate baseline secara otomatis. Pada workflow
orchestration, `register_challenger()` memeriksa model mengalahkan naive baseline.
Gate tersebut belum membuktikan candidate mengalahkan champion pada evaluation
set yang sama.

### Praktik 5C: telusuri lineage

```text
champion alias
  → model version
  → source run ID
  → parameter + metric + snapshot name + SHA256
  → DVC pipeline state + source code revision
```

Serving me-resolve alias lalu memuat artifact dengan URI version tetap, misalnya
`models:/taxi-demand-forecasting-model/2`. Angka 2 hanya contoh; gunakan version
yang terdaftar. Pinning ini menjaga metadata dan artifact selaras jika alias
berubah saat model dimuat.

**Bukti hasil:** `/model-info` memberi HTTP 200, champion menunjuk version yang
dipilih, dan peserta dapat menunjukkan run serta dataset sumbernya.

**Latihan rollback:** catat version champion sebelumnya. Jika ada version
sebelumnya yang sudah direview dan kompatibel, alias dapat diarahkan kembali
dengan script promotion yang sama. Tunggu refresh loader dan kirim request baru
untuk memeriksa versi yang benar-benar dipakai.

## 8. Sesi 6 — Serving dan kontrak API

### Alur request prediction

Client mengirim zone dan target hour. API membangun feature dari processed
demand, memuat champion melalui registry, menghasilkan prediksi, lalu mencatat
event beserta model version dan run ID. Feature tidak perlu dihitung client.

Docker image mengemas kode dan dependency. Compose me-mount `data/` dari host ke
`/app/data`, sehingga hasil script manual tersedia bagi API. Isi dataset dan
champion registry tidak dibuat otomatis hanya dengan menyalakan container.

### Praktik 6A: kirim satu request

Buka <http://localhost:8000/docs>, pilih `POST /predict`, lalu kirim:

```json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
```

**Hasil yang diperiksa:** HTTP 200, `predicted_trip_count`, version, alias, run ID,
dan URI model. Angka prediksi mengikuti model hasil training peserta.

Timestamp tanpa timezone dianggap waktu lokal NYC dan harus tepat di awal jam.
Serving membutuhkan history 168 jam sebelum target. Latency request pertama
bisa lebih besar karena model belum dimuat ke cache.

### Praktik 6B: uji input yang ditolak

Ubah target menjadi `2025-01-28T18:30:00` dan kirim kembali. Response seharusnya
422 karena granularity target adalah satu jam. Request ditolak menambah counter
HTTP, tetapi tidak menambah counter prediksi berhasil atau prediction log.

### Praktik 6C: identitas hasil inference

Buka `data/monitoring/predictions.jsonl`. Bandingkan metadata event dengan
response HTTP dan registry. Catat bahwa model version penting untuk evaluasi
setelah champion berubah.

**Checkpoint:** mengapa service dapat hidup tetapi prediction gagal? Bedakan
model yang belum tersedia, history tidak lengkap, dan request yang tidak valid.

## 9. Sesi 7 — Monitoring service dan kualitas model

### Dua pertanyaan yang berbeda

| Pertanyaan | Sinyal | Sumber |
| --- | --- | --- |
| Apakah API menerima request dengan baik? | Request rate, 4xx/5xx, latency | Middleware HTTP dan counter prediction |
| Apakah forecast masih cukup akurat? | Recent MAE, sample, threshold, evaluation age | Prediction log yang dipasangkan dengan actual demand |

Prometheus mengambil metric dari `/metrics` setiap 5 detik sesuai config repo.
Grafana menampilkan query atas metric tersebut. File summary evaluasi dibaca
oleh endpoint metrics; Grafana tidak menghitung error per prediksi sendiri.

### Praktik 7A: isi traffic operasional

```bash
uv run python scripts/generate_api_traffic.py \
  --date 2025-01-28 --start-hour 17 --end-hour 18
```

Tunggu 10–15 detik. Jika burst pertama selesai sebelum scrape pertama terhadap
counter baru, ulangi command setelah jeda. Rate memerlukan perubahan di antara
sample counter; membuka dashboard sendiri tidak menghasilkan `/predict` traffic.

Buka Prometheus dan periksa query berikut satu per satu:

```promql
up{job="taxi-api"}
```

```promql
taxi_api_requests_total{path="/predict"}
```

```promql
sum(rate(taxi_api_requests_total{path="/predict"}[1m]))
```

`up=1` berarti scrape berhasil. Counter adalah jumlah kumulatif sejak proses
API berjalan, sedangkan rate menunjukkan request per detik dalam window.
Panel latency memakai histogram dan memperkirakan quantile; p95 bukan rata-rata.

### Praktik 7B: evaluasi dengan ground truth

```bash
uv run python scripts/evaluate_predictions.py
```

Evaluasi memilih prediction champion saat ini, menghapus duplikat zone/target/
version dengan mempertahankan prediksi terakhir, lalu join actual demand pada
zone dan target hour. Record tanpa actual tidak dapat menghasilkan error.

Summary memakai maksimal 500 sample terbaru menurut target replay secara default.
Reference MAE diambil dari validation run champion; threshold default adalah
`reference_mae × 1.25`. Minimal 100 matched sample diperlukan untuk keputusan
retraining. Semua nilai ini harus dibaca bersama konteks tanggal evaluasinya.

| Status summary | Tampilan/arti | Tindakan |
| --- | --- | --- |
| `not_evaluated` | Belum ada matched actual | Periksa log, versi, dan ground truth |
| `insufficient_samples` | Error dapat dihitung, evidence masih sedikit | Tambah target/zone unik dan evaluasi lagi |
| `within_threshold` | Sample cukup, recent MAE dalam batas | Lanjutkan observasi |
| `retrain_recommended` | Sample cukup, recent MAE melewati batas | Selidiki data dan jalankan evaluasi candidate |

Ketika summary belum ada, dashboard juga menunjukkan belum dievaluasi. Nilai
MAE tidak tersedia harus dibaca sebagai belum diketahui. Error rate nol ketika
ada traffic berbeda dari error rate tidak tersedia karena tidak ada traffic.

### Praktik 7C: baca dashboard sebagai bukti

Pada [dashboard](http://localhost:3000/d/taxi-demand-mlops/taxi-demand-mlops),
periksa urutan berikut:

1. Request rate dan predictions in 5m membuktikan adanya prediction traffic.
2. Latency dan 4xx/5xx menggambarkan perilaku service.
3. Evaluation Samples membuktikan banyaknya data yang mendukung keputusan.
4. Model MAE membandingkan recent, reference, dan threshold.
5. Model Evaluation Status menunjukkan hasil aturan evaluasi.
6. Evaluation Age dan Last Evaluation menunjukkan kesegaran job evaluasi.
7. Latest Evaluated Replay Target menunjukkan batas waktu data historical.
8. Serving Model dan Evaluated Model menunjukkan sumber versi masing-masing.

Dashboard memakai timezone `America/New_York`. Tahun 2025 pada target replay
sesuai dataset, sementara timestamp job evaluasi mengikuti saat workshop berjalan.
Setelah promotion, model serving dapat sudah berubah sementara summary MAE masih
milik versi sebelumnya. Kirim prediksi baru dan jalankan evaluasi untuk versi baru.

### Praktik 7D: demo evidence yang belum cukup

Setelah ada matched actual, jalankan:

```bash
uv run python scripts/evaluate_predictions.py --min-samples 100000
```

Status seharusnya berubah menjadi `insufficient_samples` pada dataset demo ini.
MAE dapat tetap terlihat, tetapi keputusan retrain belum didukung sample minimum.
Kembalikan konfigurasi sebelum melanjutkan:

```bash
uv run python scripts/evaluate_predictions.py
```

**Latihan keputusan:** tuliskan tindakan pertama untuk masing-masing kondisi:

| Kondisi | Pertanyaan investigasi |
| --- | --- |
| Latency tinggi, MAE dalam batas | Apakah cold load, pembacaan feature, atau resource service bermasalah? |
| HTTP sukses, MAE melewati batas | Apakah actual dan feature benar, lalu apakah candidate perlu ditrain? |
| MAE rendah, evaluasi lama | Apakah hasil lama masih cukup untuk menyimpulkan kondisi saat ini? |
| Serving version berbeda dari evaluated version | Model mana yang sebenarnya mempunyai MAE tersebut? |

## 10. Sesi 8 — Airflow dan retraining

### Pekerjaan manual menjadi workflow

Repo menyediakan tiga DAG. Semua memakai `schedule=None`, sehingga run workshop
dipicu manual. DAG ini belum mempunyai jadwal harian atau trigger otomatis antar
DAG hanya karena container Airflow menyala.

| DAG | Task utama | Hasil |
| --- | --- | --- |
| `taxi_initial_training` | DVC snapshot → training → registration gate | Candidate jika mengalahkan baseline |
| `taxi_daily_replay` | Release → validate → aggregate → rebuild features | Demand dan feature sampai replay date |
| `taxi_model_monitoring` | Evaluate → maybe retrain | Summary dan, bila layak, candidate baru |

XCom membawa metadata dan path, bukan seluruh DataFrame. Logic berada di
`src/orchestration/`; DAG mengatur dependency dan entry point task.

### Praktik 8A: start Airflow

```bash
docker compose up -d --build airflow
docker compose logs --tail=100 airflow
docker compose ps airflow
```

Pada kolom `PORTS`, buka host port di sisi kiri. Contoh `127.0.0.1:18081->8080/tcp` berarti gunakan `http://localhost:18081`. Port 8080 di kanan hanya berlaku di dalam container. Credential Compose dapat dibaca dari file di container:

```bash
docker compose exec airflow cat /airflow/simple_auth_manager_passwords.json.generated
```

Jangan memasukkan credential ke laporan kelas. Pastikan browser membuka service dari project Compose ini; Airflow standalone lokal di `localhost:8080` memakai database/riwayat berbeda. DAG workshop memakai manual trigger, jadi Home belum memiliki run sampai DAG di-trigger.

### Praktik 8B: jalankan daily replay

Di UI, trigger `taxi_daily_replay` dengan `replay_date=2025-01-27`, tunggu selesai,
lalu ulangi untuk `2025-01-28`. Parameter run kedua:

```json
{
  "replay_date": "2025-01-28"
}
```

Meskipun history sudah disiapkan manual, latihan ini memperlihatkan release
daily raw batch, validation, aggregation, dan rebuild feature. Setelah Jan 28,
feature dataset mencakup data sampai cutoff yang diperlukan retraining.

**Bukti hasil:** task log dan output metadata menunjukkan tanggal yang benar;
processed demand dan feature tersedia. DAG warna hijau berarti task selesai,
tetapi peserta tetap perlu membaca nilai return dan artifact yang dihasilkan.

### Praktik 8C: optional initial training dalam container

Docker image repo tidak menyertakan `.git`. DVC stage pada DAG initial training
memerlukan mode tanpa SCM untuk runtime container ini. Sebelum memicu DAG:

```bash
docker compose exec airflow dvc config core.no_scm true --local
```

Konfigurasi ini hanya berada di container dan perlu diterapkan kembali jika
container dibuat ulang. DVC pada host tetap dipakai dalam Git checkout untuk
latihan versioning. Jangan mengartikan mode container tanpa SCM sebagai bukti
integrasi riwayat Git.

Trigger `taxi_initial_training`, baca hasil registration gate, lalu cek MLflow.
Jika model tidak mengalahkan baseline, registration dapat mengembalikan
`not_registered` meskipun task berhasil. Champion tidak dipromote otomatis.

### Praktik 8D: monitoring dan keputusan retraining

Pastikan prediction log dan actual tersedia. Trigger `taxi_model_monitoring`
dengan parameter default:

```json
{
  "degradation_multiplier": 1.25,
  "min_samples": 100,
  "recent_limit": 500
}
```

Jika retraining tidak direkomendasikan, task berhenti dengan `not_needed`.
Periksa `evaluation_status`; kondisi tanpa rekomendasi juga bisa disebabkan
sample belum cukup. Hasil ini bukan kegagalan workflow.

Jika sample cukup dan recent MAE melewati threshold, flow membuat snapshot
sampai tanggal actual terbaru yang dievaluasi, melatih baseline dan HGB,
kemudian memeriksa baseline gate sebelum registration sebagai challenger.
Validation memakai lima hari terakhir snapshot baru.

**Contoh perhitungan, bukan hasil demo yang dijanjikan:** reference 10,
multiplier 1.25, recent MAE 13, dan 120 sample berarti threshold 12.5 dan
retraining direkomendasikan. Dengan lima sample, keputusan belum cukup didukung.

Untuk mempelajari cabang rekomendasi tanpa mengubah data/log demo, baca dan
jalankan unit test yang menggunakan fixture error tinggi:

```bash
uv run pytest tests/test_monitoring.py tests/test_monitoring_orchestration.py -q
```

Test menunjukkan aturan threshold serta jalur tanpa retraining; test ini tidak
mendaftarkan candidate nyata. Candidate nyata hanya muncul jika kondisi pada
run monitoring memang terpenuhi dan gate registration lolos.

### Review candidate dan promotion

Periksa run ber-tag `retraining-validation`, snapshot, metric, dan output
registration. Bandingkan candidate dengan champion pada periode evaluasi yang
sama sebelum memilih model. MAE initial Jan 22–26 dan MAE holdout baru tidak
dapat diperlakukan sebagai perbandingan langsung yang sepenuhnya setara.

Jika candidate sudah direview, gunakan script promotion dari sesi 5. Loader
serving mengecek registry secara berkala, default sekitar 30 detik, kemudian
memuat artifact version terpilih ketika dibutuhkan. Kirim prediction baru dan
bandingkan Serving Model dengan Evaluated Model.

**Checkpoint:** trigger retraining, registration challenger, dan promotion
champion adalah tiga keputusan berbeda. Jelaskan siapa yang menghasilkan
evidence dan siapa yang memilih versi untuk serving.

## 11. Sesi 9 — CI/CD untuk kode dan container

### Praktik 9A: baca workflow repo

Buka `.github/workflows/ci.yml` dan `.github/workflows/cd.yml`.

| Pemeriksaan/aksi | Fungsi dalam repo |
| --- | --- |
| Branch policy | PR ke develop dari branch kerja; PR ke main dari develop |
| Ruff | Masalah lint dan import |
| Pytest | Perilaku data, feature, API, registry, dan monitoring |
| MkDocs strict | Dokumentasi dapat dibangun dengan referensi yang valid |
| Docker build matrix | Target API, MLflow, dan Airflow dapat dibangun |
| Container Delivery | Image diterbitkan ke GHCR melalui workflow publish |

Pada jalur otomatis, Container Delivery dipicu setelah CI sukses untuk push ke
`main` dan checkout commit yang diuji. Repo juga menyediakan `workflow_dispatch`
untuk publish manual. Workflow ini belum menjalankan rollout ke server deployment.

### Praktik 9B: jalankan quality checks lokal

```bash
uv run ruff check src api scripts tests
uv run pytest -q
uv run --group docs mkdocs build --strict
docker compose config --quiet
```

Peserta tidak perlu mengirim PR atau publish image ke repo bersama. Fasilitator
dapat memakai contoh CI run yang sudah ada untuk membaca job dan log.

**Latihan:** tentukan apakah tiap perubahan berikut termasuk lifecycle kode,
lifecycle model, atau keduanya:

- Memperbaiki schema request API.
- Mengganti champion ke model version yang sudah terdaftar.
- Mengubah semantic lag feature lalu retrain.
- Memperbaiki query dashboard tanpa mengganti artifact model.

Tag image berbasis commit SHA membantu menelusuri runtime kode. Model version
mengidentifikasi artifact model. Mengganti salah satunya tidak selalu mengganti
yang lain.

## 12. Sesi 10 — Laporan hasil peserta

Setiap pasangan membuat satu laporan singkat dengan bukti berikut. Jangan
menyalin angka contoh sebagai hasil praktik.

```markdown
# Hasil Workshop — Nama Peserta

## Data dan experiment
- Revision kode yang dipakai:
- Snapshot dan SHA256:
- Periode train/validation:
- Run ID baseline / MAE / RMSE:
- Run ID model / MAE / RMSE:

## Serving
- Champion model version dan source run ID:
- Contoh request dan response prediction:
- Hasil request invalid:

## Monitoring dan keputusan
- Evaluation count / minimum sample:
- Recent MAE / reference MAE / threshold:
- Evaluation status:
- Waktu job evaluasi / latest replay target:
- Serving model / evaluated model:
- Tindakan yang disarankan beserta alasannya:

## Reproducibility dan workflow
- Hasil dvc status:
- DAG yang dijalankan dan output bisnisnya:
- Satu keterbatasan implementasi dan usulan perbaikan:
```

### Rubrik penilaian

| Aspek | Bobot | Kriteria |
| --- | ---: | --- |
| Data dan leakage | 20% | Menjelaskan cutoff, warm-up, dan batas history |
| Experiment dan lineage | 25% | Membandingkan baseline dan menelusuri champion ke dataset |
| Serving | 15% | Request berhasil, input invalid ditolak, metadata cocok |
| Monitoring dan keputusan | 25% | Membaca sample, freshness, MAE, dan sumber versi |
| Orchestration dan CI/CD | 15% | Menjelaskan task outcome dan membedakan lifecycle kode/model |

Kelulusan praktik berarti evidence utama tersedia dan keputusan dapat dijelaskan.
Model dengan MAE paling kecil bukan satu-satunya ukuran keberhasilan workshop.

## 13. Troubleshooting yang dipakai selama kelas

| Gejala | Kemungkinan penyebab | Pemeriksaan berikutnya |
| --- | --- | --- |
| Module tidak ditemukan | Command memakai interpreter global | Jalankan melalui `uv run` dan cek `uv sync` |
| Docker tidak terhubung | Engine/context belum siap | `docker info` dan `docker context ls` |
| Port 8000 sudah dipakai | Docs dan API memakai port yang sama | Jalankan docs pada port 8002 |
| Tracking gagal | Host script dan container memakai alamat berbeda | Host memakai localhost; container memakai service hostname |
| `/model-info` memberi 503 | Champion belum ada atau server registry tidak tersedia | Periksa MLflow, registration, dan promotion |
| Prediction memberi 422 | Target/zone tidak valid atau history bolong | Baca response; cek demand harian dan target awal jam |
| DVC gagal di Airflow Docker | Tidak ada `.git` di image | Terapkan konfigurasi local no-SCM pada sesi 8C |
| Grafana tidak menunjukkan traffic | Belum ada HTTP prediction atau scrape belum menangkap kenaikan | Periksa target UP dan ulangi traffic setelah scrape |
| MAE belum tersedia | Belum ada actual match untuk model yang dievaluasi | Periksa prediction log, versi, demand, dan summary |
| Sample tidak bertambah saat request diulang | Deduplication zone/target/version | Tambah target hour unik jika perlu memperluas evidence |
| Summary milik versi lama | Champion berganti sesudah evaluasi | Prediksi dan evaluasi versi baru; periksa kedua tabel model |

Untuk log service:

```bash
docker compose logs --tail=100 mlflow api prometheus grafana
```

Untuk berhenti tanpa menghapus state data dan named volume:

```bash
docker compose down
```

## 14. Catatan fasilitator

### Sebelum peserta datang

1. Jalankan panduan Grafana pada revision workshop yang akan dipakai, termasuk
   training, artifact reload, HTTP prediction, dan evaluasi dengan actual.
2. Catat run ID, model version, serta metric hasil preflight; hasil peserta dapat
   berbeda jika input/dependency berubah.
3. Periksa engine Docker, target Prometheus, dan dashboard provisioning.
4. Siapkan contoh CI run dan, jika ada, contoh challenger yang sudah direview.
5. Pastikan sesi Airflow daily replay Jan 27 lalu Jan 28 dapat berjalan. Terapkan
   workaround DVC container jika initial training DAG akan didemokan.

### Saat mengajar

- Tanyakan alasan sebuah tool diperlukan sebelum membuka UI-nya.
- Berhenti di checkpoint bila model/data belum siap; UI service yang terbuka
  belum cukup menjadi bukti checkpoint inference.
- Bedakan hasil real peserta dengan angka ilustrasi dalam modul.
- Gunakan demo sample kurang dan request invalid untuk memperlihatkan status
  yang berbeda; tidak perlu memanipulasi actual agar dashboard terlihat bagus.
- Jika retrain tidak terpicu, baca summary dan gunakan fixture test untuk membahas
  cabang threshold. Jangan menjanjikan candidate baru untuk setiap DAG run.

### Kunci diskusi singkat

| Pertanyaan | Jawaban yang dicari |
| --- | --- |
| Mengapa warm-up tujuh hari? | Feature terjauh memerlukan lag 168 jam |
| Mengapa shift sebelum rolling? | Actual target tidak boleh menjadi feature |
| Mengapa baseline dan HGB memakai split sama? | Perbandingan model perlu konteks evaluasi yang sama |
| Mengapa Git dan DVC masih perlu MLflow? | Source/data state dan catatan experiment mempunyai tanggung jawab berbeda |
| Mengapa `/health` sukses belum menjamin inference? | Endpoint ini tidak memverifikasi champion dan kelengkapan history |
| Mengapa request berulang tidak menambah sample unik? | Evaluasi mempertahankan prediksi terakhir per zone/target/version |
| Mengapa `retrain_recommended=false` belum tentu model sehat? | Actual bisa belum ada atau sample belum cukup |
| Mengapa p95 rendah belum menjamin forecast baik? | Latency mengukur service; MAE memerlukan ground truth |
| Mengapa Serving Model dan Evaluated Model bisa berbeda? | Promotion dan job evaluasi berjalan pada waktu berbeda |
| Mengapa DAG sukses belum berarti candidate diregister? | Return bisnis dapat `not_registered` atau `not_needed` |
| Mengapa candidate baru belum langsung champion? | Baseline gate belum menggantikan review dan perbandingan champion |
| Mengapa publish image belum berarti deployment selesai? | Workflow repo menerbitkan image, tanpa rollout ke server |

## 15. Batas implementasi dan latihan lanjutan

Workshop memakai filesystem lokal, SQLite metadata MLflow, Airflow standalone,
dan Compose. Replay berjalan sesudah daily file tersedia; fitur dibatasi sebelum
target, tetapi repo belum menyimulasikan latency kedatangan data secara real time.

Monitoring model saat ini mengevaluasi error agregat terhadap threshold sederhana.
Belum ada deteksi drift feature, alert routing, atau analisis kualitas per zone.
Snapshot/lineage juga belum otomatis menyimpan semua informasi revision kode dan
environment yang diperlukan untuk reproduksi lintas mesin.

| Latihan lanjutan | Pertanyaan desain |
| --- | --- |
| Dependency yang terkunci dan digunakan image | Apakah host, CI, dan container memasang versi yang sama? |
| Validasi grid offline | Bagaimana mendeteksi duplicate/missing hour sebelum shift baris? |
| Jadwal dan dependency antar DAG | Bagaimana memastikan evaluasi menunggu actual tersedia? |
| Retraining idempotent | Bagaimana retry/run berulang tidak membuat candidate duplikat? |
| Readiness inference | Apa yang perlu dicek selain proses API hidup? |
| Alert dan freshness | Kapan operator diberi tahu tentang scrape gagal atau evaluasi lama? |
| Evaluasi per zone dan common holdout | Apakah kualitas agregat menyembunyikan area yang buruk? |
| Storage dan model review bersama | Bagaimana dataset, artifact, dan approval dibagikan antar tim? |

Pilih satu latihan, jelaskan perubahan yang diusulkan, dan tentukan bukti yang
akan dipakai untuk memverifikasi perbaikannya.

## 16. Bacaan pendamping

- [Panduan Grafana dari kondisi kosong](10-hands-on/dashboard-quickstart.md).
- [Feature & model design](02-use-case/feature-design.md).
- [Step DVC](10-hands-on/step-03-dvc.md) dan
  [model registry](06-experiment-tracking/model-registry.md).
- [Monitoring Grafana](09-monitoring/grafana.md) dan
  [step retraining](10-hands-on/step-10-retraining.md).
- [Docker Compose command reference](https://github.com/docker/compose/blob/main/docs/reference/compose.md).
- [DVC pipeline reproduction](https://dvc.org/doc/command-reference/repro) dan
  [mode tanpa Git](https://dvc.org/doc/command-reference/init).
- [Airflow standalone](https://airflow.apache.org/docs/apache-airflow/stable/start.html).
- [MLflow skops serialization](https://github.com/mlflow/mlflow/blob/v3.16.1/docs/docs/classic-ml/tracking/pickle-free-models/index.mdx).
