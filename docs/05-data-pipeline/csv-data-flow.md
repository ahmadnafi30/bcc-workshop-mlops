# CSV Data Flow: Buka Data, Ikuti Prosesnya

Workshop menggunakan **Parquet hanya untuk download sumber TLC**. Semua dataset hasil konversi dan proses berikutnya berupa **CSV** agar peserta dapat melihat tabel langsung.

## File apa yang harus dibuka?

| Tahap | File contoh | Satu baris berarti |
|---|---|---|
| Download | `data/source/tlc/yellow_tripdata_2025-01.parquet` | Arsip asli TLC; gunakan CSV konversi untuk inspeksi |
| Konversi | `data/source/tlc/yellow_tripdata_2025-01.csv` | Satu perjalanan, seluruh kolom sumber |
| Replay source | `data/source/replay/yellow_tripdata_2025-01.csv` | Satu pickup Manhattan yang valid |
| Raw batch | `data/raw/trips/2025-01-27.csv` | Satu perjalanan pada tanggal replay |
| Demand | `data/processed/demand/2025-01-27.csv` | Satu zona pada satu jam |
| Features | `data/features/taxi_demand_features.csv` | Satu target hour beserta calendar, lag, rolling, dan actual |
| Snapshot | `data/snapshots/training/taxi_demand_2025-01-26.csv` | Contoh model-ready untuk periode eksperimen |
| Evaluation | `data/monitoring/evaluations.csv` | Satu pasangan prediction dan actual beserta error |

Prediction log tetap JSONL dan summary monitoring tetap JSON karena keduanya adalah log/metadata, bukan tabel Parquet yang perlu dimigrasikan. Model artifacts juga tetap memakai format model yang didukung MLflow.

## Baca dataset sebagai manusia

~~~powershell
Get-Content data/snapshots/training/taxi_demand_2025-01-26.csv -TotalCount 6
~~~

Atau tampilkan beberapa kolom sebagai tabel:

~~~powershell
uv run python -c "import pandas as pd; d=pd.read_csv('data/snapshots/training/taxi_demand_2025-01-26.csv'); print(d[['timestamp','zone_id','lag_1h','lag_24h','lag_168h','target_trip_count']].head(10).to_string(index=False))"
~~~

Gunakan import Text/CSV dengan delimiter comma jika Excel tidak memisahkan kolom otomatis. CSV bulanan dapat melebihi batas baris spreadsheet; lihat sebagian baris atau gunakan daily CSV yang lebih kecil.

## Snapshot itu apa?

Snapshot adalah dataset yang disimpan untuk suatu cutoff. File berisi **features dan target**, kemudian training code melakukan time-based split:

~~~text
params.json: history Jan 1, cutoff Jan 26
                     ↓
Snapshot model-ready Jan 8–26
         ↙                       ↘
Train Jan 8–21          Validation Jan 22–26
~~~

Jan 1–7 menyediakan history untuk lag 168 jam. Cutoff snapshot bukan akhir train split. Nama bertanggal menunjukkan periodenya; hash mencatat identitas isinya. File dapat ditulis ulang, sehingga perubahan metadata tetap perlu dicatat di Git.

## DVC menghubungkan apa?

~~~text
Daily demand CSV
        ↓ build_training_features
Training features CSV
        ↓ create_training_snapshot
Training snapshot CSV
        ↓ model training
MLflow experiment
~~~

| Bagian | Fungsi |
|---|---|
| `params.json` | Periode history dan cutoff |
| `dvc.yaml` | Command, dependency, parameter, dan output stage |
| `dvc.lock` | Fingerprint dari keadaan stage yang direproduce |
| `.dvc/cache/files` | Isi output yang disimpan secara lokal |
| `.dvc/cache/runs` | Catatan stage untuk menggunakan kembali hasil sebelumnya |

Hash berbeda untuk file berbeda. Dependency Python juga mempunyai hash karena perubahan code dapat mengubah hasil. Run cache DVC berbeda dari MLflow run dan Airflow DAG run.

## Apa fungsi code data_versioning?

| Modul/fungsi | Peran |
|---|---|
| `pipeline_config.load_training_dates` | Baca `params.json`, validasi urutan tanggal |
| `pipeline_config.training_snapshot_path` | Tentukan lokasi snapshot CSV sesuai cutoff |
| `pipeline_files.read_csv_dataset` | Baca CSV dan pulihkan tipe datetime |
| `pipeline_files.iter_csv_chunks` | Baca monthly CSV secara bertahap |
| `pipeline_files.file_fingerprint` | Hitung SHA-256 isi file |
| `pipeline_files.write_csv_atomic` | Publikasikan satu CSV setelah penulisan selesai |
| `pipeline_files.write_csv_chunks_atomic` | Tulis banyak chunk menjadi satu CSV secara atomic |
| `pipeline_files.write_json_atomic` | Simpan metadata JSON melalui file sementara |
| `snapshot.build_snapshot_name` | Buat nama CSV berdasarkan cutoff |
| `snapshot.create_training_snapshot` | Filter sampai akhir cutoff, cek tidak kosong, urutkan data |
| `snapshot.calculate_file_sha256` | Fingerprint snapshot yang dipakai training |
| `snapshot.describe_snapshot` | Nama, hash, rows, zones, dan rentang waktu |

DVC memakai MD5 pada lock ini; helper project memakai SHA-256 untuk lineage/cache. Kedua fingerprint tetap mengikuti isi file. CSV yang diekspor dengan susunan atau encoding berbeda bisa mempunyai hash berbeda meskipun tabel terlihat serupa.

## Command utama

~~~powershell
uv run python scripts/bootstrap_data.py --months 2025-01
uv run python scripts/prepare_historical_demand.py --start-date 2025-01-01 --end-date 2025-01-26
uv run dvc dag
uv run dvc repro create_training_snapshot
uv run python scripts/train_with_mlflow.py --search
~~~

Training memerlukan MLflow tracking server yang dapat diakses. Menjalankan DVC saja belum melatih model atau menjalankan API. Untuk demo lengkap, ikuti [Dashboard Quickstart](../10-hands-on/dashboard-quickstart.md).

## Hal yang perlu dicatat saat workshop

- Konversi dilakukan satu kali setelah download, dengan chunk untuk membatasi memori.
- CSV biasanya membutuhkan ruang disk lebih besar. File daily/features jauh lebih kecil daripada full monthly source.
- `deps` memeriksa perubahan dependency; agar isi data sumber dapat dibagikan lewat DVC, sumber tersebut perlu dilacak tersendiri atau diadakan kembali melalui bootstrap.
- Dataset tidak otomatis masuk Git karena formatnya sekarang teks. Gunakan DVC metadata untuk versioning.
- Data lama dapat dimigrasikan melalui `scripts/migrate_data_to_csv.py`. Arsip legacy berada di luar folder dataset aktif.
