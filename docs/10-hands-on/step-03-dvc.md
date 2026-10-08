# Step 3: DVC dari CSV Sederhana ke Training Snapshot

Pada sesi ini kita mulai dengan file kecil yang dapat dibuka langsung. Setelah memahami versioning, kita mengikuti pipeline CSV yang dipakai model taxi.

**Terminal:** PowerShell, dari root repository. Dependency sudah terpasang melalui `uv sync`.

## Bagian A: Demo add, push, pull, dan restore

### 1. Periksa apakah DVC sudah aktif

```powershell
uv run dvc root
uv run dvc remote list
```

Repo workshop sudah mempunyai `.dvc`; tidak perlu menjalankan `dvc init` lagi. Error `.dvc exists` berarti project sudah diinisialisasi.

### 2. Buat CSV demo

Jika `data/simple_case/data.csv` sudah berisi latihanmu sebelumnya, gunakan file itu dan lewati command pembuatan berikut.

```powershell
New-Item -ItemType Directory -Force data/simple_case | Out-Null
@'
zone_id,trip_count
161,100
162,80
'@ | Set-Content -Encoding utf8 data/simple_case/data.csv
Get-Content data/simple_case/data.csv
```

Ini hanya tabel simulasi, bukan dataset yang dilatih oleh model taxi.

### 3. Catat versi pertama

```powershell
uv run dvc add data/simple_case/data.csv
Get-Content data/simple_case/data.csv.dvc
git add data/simple_case/data.csv.dvc
if (Test-Path data/simple_case/.gitignore) { git add data/simple_case/.gitignore }
git commit -m "Demo DVC: record CSV version 1"
$demoV1 = git rev-parse HEAD
```

| Hasil | Fungsinya |
|---|---|
| `data.csv` | Isi data yang dapat dibaca |
| `data.csv.dvc` | Metadata hash dan lokasi file |
| `data/simple_case/.gitignore` | Mencegah CSV tersebut masuk Git |
| DVC cache | Menyimpan isi versi pertama |
| Git commit | Menyimpan metadata versi pertama |

Catat nilai `$demoV1` jika akan membuka terminal baru. Commit lokal ini belum mengirim apa pun ke GitHub.

### 4. Pilih remote default, lalu push

```powershell
uv run dvc remote list
```

Jika belum ada `demo-local`:

```powershell
uv run dvc remote add --local -d demo-local D:/bcc-dvc-storage
```

Jika remote tersebut sudah ada:

```powershell
uv run dvc remote default --local demo-local
```

Kemudian:

```powershell
uv run dvc push data/simple_case/data.csv.dvc
```

Push menggunakan remote default tanpa perlu `-r`. Metadata tetap di Git; isi CSV masuk storage DVC. Push ulang tanpa perubahan bisa menampilkan bahwa semua file sudah up to date.

### 5. Tambahkan data dan catat versi kedua

```powershell
Add-Content data/simple_case/data.csv '163,120'
Get-Content data/simple_case/data.csv
uv run dvc add data/simple_case/data.csv
Get-Content data/simple_case/data.csv.dvc
git add data/simple_case/data.csv.dvc
git commit -m "Demo DVC: record CSV version 2"
$demoV2 = git rev-parse HEAD
uv run dvc push data/simple_case/data.csv.dvc
```

Hash berubah setelah **isi file yang sudah disimpan** berubah. Jika tetap sama, periksa path yang diedit, simpan editor, lalu lihat `Get-Content` pada file yang sama.

### 6. Pulihkan file workspace

Simpan salinan file saat ini sebelum meminta DVC memulihkannya. Pilih nama backup baru jika file backup berikut sudah ada.

```powershell
Move-Item data/simple_case/data.csv data/simple_case/data.csv.backup
uv run dvc pull data/simple_case/data.csv.dvc
Get-Content data/simple_case/data.csv
```

CSV versi kedua muncul kembali sesuai metadata aktif. Jika isi masih tersedia di cache lokal, DVC tidak perlu mengunduh ulang dari remote. `dvc pull` memastikan isi tersedia dan mengembalikan file workspace.

### 7. Restore versi pertama tanpa mengganti seluruh repo

```powershell
git restore --source=$demoV1 -- data/simple_case/data.csv.dvc
uv run dvc pull data/simple_case/data.csv.dvc
Get-Content data/simple_case/data.csv
```

Hasil sekarang memiliki dua baris data seperti versi pertama. Git memilih metadata lama; DVC memulihkan isi yang ditunjuk metadata itu.

Kembali ke versi kedua:

```powershell
git restore --source=$demoV2 -- data/simple_case/data.csv.dvc
uv run dvc pull data/simple_case/data.csv.dvc
```

Jika cache lokal sudah mempunyai isi yang dibutuhkan, `dvc checkout data/simple_case/data.csv.dvc` juga dapat digunakan. Restore ini dapat mengganti isi file workspace; simpan perubahan yang ingin dipertahankan terlebih dahulu.

## Bagian B: DVC yang benar-benar dipakai repo taxi

### 1. Siapkan input CSV

```powershell
uv run python scripts/bootstrap_data.py --months 2025-01
uv run python scripts/prepare_historical_demand.py --start-date 2025-01-01 --end-date 2025-01-26
```

Bootstrap mendownload Parquet resmi TLC, langsung mengonversi semua kolom ke CSV, lalu membuat replay source CSV. History preparation membaca replay CSV dan menghasilkan daily demand CSV.

### 2. Baca konfigurasi dan graph

```powershell
Get-Content params.json
Get-Content dvc.yaml
uv run dvc dag
```

Dengan konfigurasi default:

```json
{
  "data": {
    "history_start": "2025-01-01",
    "training_cutoff": "2025-01-26"
  }
}
```

`history_start` menentukan awal history untuk membangun lag/rolling. `training_cutoff` menentukan batas akhir snapshot, termasuk hari tersebut.

### 3. Jalankan dua stage

```powershell
uv run dvc repro create_training_snapshot
```

DVC menjalankan upstream `build_training_features` jika diperlukan, lalu membuat snapshot. Jika dependency, params, code, dan output sesuai catatan sebelumnya, stage dapat di-skip atau menggunakan cache.

| Stage | Input utama | Output |
|---|---|---|
| `build_training_features` | Daily demand CSV dan periode `params.json` | `data/features/training/taxi_demand_features.csv` |
| `create_training_snapshot` | Training features CSV dan cutoff | `data/snapshots/training/taxi_demand_2025-01-26.csv` |

Training features dipisahkan dari `data/features/taxi_demand_features.csv` yang dapat terus berkembang saat replay. Keduanya sekarang readable CSV.

### 4. Buka snapshot dan lock

```powershell
Get-Content data/snapshots/training/taxi_demand_2025-01-26.csv -TotalCount 6
Get-Content dvc.lock
uv run dvc status
```

Snapshot berisi features **dan** `target_trip_count`. History Jan 1–7 membangun lag satu minggu; model-ready rows mulai Jan 8. Training code memakai lima hari terakhir sebagai validation, sehingga default snapshot dibagi menjadi train Jan 8–21 dan validation Jan 22–26.

Lock mencatat fingerprint tiap dependency dan output. Hash folder berakhiran `.dir` menunjuk kumpulan file, bukan satu CSV. Catatan `.dvc/cache/runs` adalah cache pipeline, bukan daftar MLflow training runs.

### 5. Simpan metadata dan isi output

Setelah remote default tersedia:

```powershell
uv run dvc push build_training_features create_training_snapshot
git add dvc.yaml dvc.lock params.json
if (Test-Path data/features/training/.gitignore) { git add data/features/training/.gitignore }
if (Test-Path data/snapshots/training/.gitignore) { git add data/snapshots/training/.gitignore }
git commit -m "Record CSV training snapshot"
```

Daily demand merupakan dependency stage, sehingga isinya tidak otomatis ikut diupload. Untuk reproduksi dari awal, bootstrap dan siapkan daily demand lagi. Untuk memperoleh output yang sudah dilacak pada versi Git tertentu, gunakan metadata versi tersebut lalu `uv run dvc pull`.

### 6. Buat snapshot dengan cutoff baru

Siapkan dulu semua daily demand hingga tanggal yang dipilih:

```powershell
uv run python scripts/prepare_historical_demand.py --start-date 2025-01-01 --end-date 2025-01-28
```

Ubah hanya `data.training_cutoff` menjadi `2025-01-28` di `params.json`, kemudian:

```powershell
uv run dvc repro create_training_snapshot
```

Output sekarang `taxi_demand_2025-01-28.csv`. Catat perubahan lock dan params di Git serta push DVC output jika versi ini ingin disimpan. Jangan memilih cutoff demo masa depan yang belum mempunyai ground truth.

## Setelah snapshot siap

```powershell
uv run python scripts/train_with_mlflow.py --search
```

Command ini menjalankan eksperimen CPU dan mencatat dataset identity di MLflow. Tracking server perlu aktif. DVC sendiri belum melatih model, mempromosikan champion, atau menjalankan API.

Lanjutkan ke [Experiment Tracking](../06-experiment-tracking/experiment-tracking.md) dan [panduan CSV Data Flow](../05-data-pipeline/csv-data-flow.md).
