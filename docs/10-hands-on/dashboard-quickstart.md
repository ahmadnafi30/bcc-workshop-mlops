# Mengisi Dashboard Grafana dari Kondisi Kosong

Panduan ini menjalankan alur **data → training → champion → HTTP traffic →
evaluasi → Grafana** secara manual. Cocok untuk demo pertama atau mengecek
dashboard sebelum sesi workshop. Airflow belum diperlukan.

Untuk materi konsep, latihan, dan panduan fasilitator, baca
[Modul Workshop](../workshop-module.md).

## Sebelum mulai

- Jalankan semua command dari root repository.
- Gunakan terminal Bash di Linux, macOS, atau WSL2.
- Siapkan Git, uv, Docker Engine/Desktop yang aktif, dan Docker Compose.
- Pastikan internet tersedia untuk dependency, image, dan dataset TLC Januari.
- Panduan memakai port dan nama model default di `docker-compose.yml`.

Jika menggunakan PowerShell, sesuaikan sintaks environment variable. Command
Python tetap sama. Jangan menjalankan server MLflow kedua pada port 5000.

## 1. Siapkan environment Python

Kalau repo belum tersedia:

```bash
git clone https://github.com/ahmadnafi30/bcc-workshop-mlops.git
cd bcc-workshop-mlops
```

Install dependency dan cek environment:

```bash
uv sync
uv run python --version
uv run python scripts/doctor.py
```

**Hasil yang diperiksa:** Python 3.11 dan semua import wajib berstatus `OK`.
Doctor mengecek keberadaan Docker CLI; kesiapan daemon diperiksa di langkah 2.

## 2. Jalankan service

Siapkan folder state pada host sebelum membuat container:

```bash
mkdir -p .mlflow/artifacts data
docker info
docker compose up -d --build grafana
docker compose ps
```

Compose ikut menjalankan dependency Grafana: Prometheus, API, dan MLflow.
Kalau stack sudah berjalan, command yang sama dapat dipakai untuk menerapkan
perubahan image dan konfigurasi repo.

| Service | Alamat | Yang diperiksa |
| --- | --- | --- |
| MLflow | <http://localhost:5000> | UI tracking dapat dibuka |
| API health | <http://localhost:8000/health> | `status` bernilai `ok` |
| Swagger | <http://localhost:8000/docs> | Endpoint API tersedia |
| Prometheus | <http://localhost:9090> | Target `taxi-api` berstatus `UP` |
| Grafana | <http://localhost:3000/d/taxi-demand-mlops/taxi-demand-mlops> | Dashboard tersedia |

API health bisa `ok` sementara model belum tersedia. Di tahap ini,
`/model-info` bisa mengembalikan 503 dan dashboard masih kosong.

Arahkan script host ke server MLflow Docker:

```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
```

Pertahankan terminal ini untuk langkah berikutnya. Jika membuka terminal baru,
set kembali variable tersebut. Container API memakai alamat internal
`http://mlflow:5000` dari Compose.

## 3. Download dan siapkan data

```bash
uv run python scripts/bootstrap_data.py --months 2025-01

uv run python scripts/prepare_historical_demand.py \
  --start-date 2025-01-01 --end-date 2025-01-28
```

Bootstrap mengunduh lookup zone dan data Yellow Taxi, lalu menyiapkan replay
source CSV untuk Manhattan. Download asli tetap Parquet; bootstrap langsung
mengonversi semua kolom ke CSV sebelum filtering. Konversi/filtering memakai
chunk agar penggunaan memori terkendali.

**Hasil yang diperiksa:** metadata zone, replay source Januari, dan file
`data/processed/demand/2025-01-28.csv` tersedia. Script history juga menyiapkan
hari-hari sebelumnya yang dibutuhkan oleh lag sampai 168 jam.

## 4. Buat features dan snapshot CSV

Pastikan `params.json` memakai history Jan 1 dan cutoff Jan 26 untuk demo ini.

```bash
uv run dvc repro create_training_snapshot
uv run python scripts/build_features.py \
  --start-date 2025-01-01 --end-date 2025-01-28 --force
```

DVC membuat training features terpisah dan snapshot Jan 26. Command kedua
membangun features operasional hingga Jan 28 untuk replay/retraining.

**Hasil yang diperiksa:**

- `data/features/training/taxi_demand_features.csv` terbentuk.
- `data/snapshots/training/taxi_demand_2025-01-26.csv` terbentuk.
- `data/features/taxi_demand_features.csv` mempunyai history operasional.
- Output snapshot menampilkan rows, zones, rentang waktu, dan SHA-256.

Cutoff snapshot initial tetap Jan 26. Jan 27–28 disiapkan untuk inference dan
ground truth. CSV snapshot berisi features beserta target; training membaginya
menjadi train Jan 8–21 dan validation Jan 22–26.

```powershell
Get-Content data/snapshots/training/taxi_demand_2025-01-26.csv -TotalCount 6
```

Untuk penjelasan file tiap tahap, baca [CSV Data Flow](../05-data-pipeline/csv-data-flow.md).

## 5. Train dan catat model run ID

```bash
uv run python scripts/train_with_mlflow.py
```

Training menghasilkan dua run: baseline naive 24 jam dan model HGB. Contoh
struktur output berikut menggunakan placeholder, bukan nilai hasil training:

```text
baseline -> MAE ..., run BASELINE_RUN_ID
model    -> MAE ..., run MODEL_RUN_ID
model uri: runs:/MODEL_RUN_ID/model
```

**Salin run ID dari baris `model`, bukan `baseline`.** Buka MLflow untuk
membandingkan MAE/RMSE, dataset SHA256, parameter, dan artifact model.

Model Poisson HGB menggunakan serialization `skops` dengan daftar trusted types
terbatas yang didefinisikan dalam repo. Jika environment lama belum mendukung
parameter ini, jalankan kembali `uv sync` sesuai `pyproject.toml`.

## 6. Register dan promote ke champion

Ganti teks `RUN_ID_MODEL` dengan run ID yang baru disalin:

```bash
uv run python scripts/register_model.py --run-id "RUN_ID_MODEL"
```

Output registration menampilkan `name`, `version`, dan alias `challenger`.
Review hasil model sebelum promotion. Script registration manual tidak
otomatis memeriksa apakah model mengalahkan baseline.

Ganti `VERSI_MODEL` dengan nilai `version` hasil registration:

```bash
uv run python scripts/promote_model.py --version "VERSI_MODEL"
```

Jangan menganggap version selalu 1. Buka <http://localhost:8000/model-info>.
**Hasil yang diperiksa:** HTTP 200, alias `champion`, serta version dan run ID
yang sesuai. Setelah mengganti champion yang sudah di-cache, beri waktu sampai
sekitar 30 detik untuk pengecekan registry berikutnya.

## 7. Kirim prediction traffic melalui HTTP

```bash
uv run python scripts/generate_api_traffic.py \
  --date 2025-01-28 --start-hour 17 --end-hour 18
```

**Hasil yang diperiksa:** output menunjukkan request berhasil dan
`data/monitoring/predictions.jsonl` mulai terisi.

Script mengirim request untuk semua Manhattan zone pada jam 17 dan 18. API
menggunakan hanya history sebelum masing-masing target hour. Karena ini replay,
file actual pada target hour sudah tersedia untuk evaluasi sesudahnya.

Tunggu 10–15 detik agar Prometheus melakukan beberapa scrape. Jika seluruh
burst pertama selesai sebelum counter pertama di-scrape, panel rate/increase
bisa masih nol. Jalankan command traffic sekali lagi setelah jeda tersebut.

Request berulang menambah counter HTTP, tetapi evaluasi memakai prediksi
terakhir untuk kombinasi zone, target hour, dan model version yang sama.

## 8. Evaluasi dan buka Grafana

```bash
uv run python scripts/evaluate_predictions.py
```

**Hasil yang diperiksa:** jumlah evaluasi lebih dari nol, recent MAE tersedia,
dan artifact berikut terbentuk:

```text
data/monitoring/evaluations.csv
data/monitoring/performance_summary.json
```

Refresh [dashboard Grafana](http://localhost:3000/d/taxi-demand-mlops/taxi-demand-mlops)
setelah scrape berikutnya. Periksa:

- Request rate, prediction count, dan latency setelah HTTP traffic.
- **Serving Model (Last Prediction)** untuk versi yang menghasilkan prediksi.
- **Model MAE** untuk recent, reference, dan threshold.
- **Evaluation Samples** dan **Model Evaluation Status**.
- **Evaluated Model** untuk versi sumber MAE.
- Waktu job evaluasi dan target historical replay.

Status hasil evaluasi mengikuti data: sample kurang, dalam batas, atau perlu
retrain. Hasil demo tidak harus selalu berwarna hijau.

## Kalau masih kosong atau gagal

| Gejala | Periksa | Tindakan |
| --- | --- | --- |
| Docker tidak bisa terhubung | `docker info` dan context yang dipilih | Aktifkan engine dan gunakan context engine yang tersedia |
| Service belum siap | `docker compose ps` | Baca `docker compose logs --tail=100 mlflow api prometheus grafana` |
| `/model-info` memberi 503 | Run ID, registration, alias, tracking URI | Register model HGB lalu promote ke `champion` pada server yang sama |
| `/predict` memberi 422 | Isi response | Lengkapi history Jan 1–28, gunakan zone Manhattan dan target tepat awal jam |
| `/predict` berhasil tetapi graph kosong | Target Prometheus dan rentang waktu Grafana | Pastikan target `taxi-api` UP, pilih Last 30 minutes, ulangi traffic setelah scrape |
| MAE belum tersedia | Prediction log, versi model, dan actual demand | Jalankan evaluasi setelah prediction dan ground truth tersedia |
| Sample masih kurang | `evaluation_count` dan `min_samples` | Gunakan target hour/zone baru; request duplikat tidak menambah sample unik |
| Permission denied pada file mount | Pemilik `.mlflow/` atau `data/` | Sesuaikan izin folder untuk user `app` UID 1000; jangan menghapus state untuk menyembunyikan error |

## Setelah demo

Untuk menghentikan stack:

```bash
docker compose down
```

Data host dan named volumes tetap tersimpan karena command tidak memakai `-v`.
Untuk demo berikutnya, jalankan service, kirim traffic baru, lalu evaluasi lagi.
Panel **Predictions in 5m** menunjukkan window berjalan, sehingga wajar turun
setelah tidak ada request baru.
