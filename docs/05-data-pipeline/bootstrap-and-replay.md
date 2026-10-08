# Bootstrap & Replay: Download Sekali, Proses dengan CSV

## Peta perjalanan data

~~~text
Official TLC monthly Parquet
        ↓ download + convert
Full monthly CSV
        ↓ filter Manhattan
Replay monthly CSV
        ↓ release one date
Raw daily CSV
        ↓ validate + aggregate
Daily demand CSV
        ↓ build lag/calendar/rolling features
Features CSV
        ↓ choose cutoff
Training snapshot CSV
~~~

Parquet hanya berada pada batas download/conversion. Aggregation, replay, features, snapshot, training, serving history, dan evaluation menggunakan CSV.

## 1. Bootstrap satu bulan

Jalankan dari root repository:

~~~powershell
uv run python scripts/bootstrap_data.py --months 2025-01
~~~

Bootstrap menghasilkan:

~~~text
data/metadata/taxi_zone_lookup.csv
data/source/tlc/yellow_tripdata_2025-01.parquet  ← download asli
data/source/tlc/yellow_tripdata_2025-01.csv      ← seluruh kolom sumber
data/source/replay/yellow_tripdata_2025-01.csv   ← compact Manhattan pickups
~~~

Default tanpa `--months` menyiapkan Januari, Februari, dan Maret. Untuk sesi pengantar, satu bulan cukup dan lebih cepat.

`download_monthly_trip_data()` mengunduh Parquet lalu memanggil converter CSV. Converter memakai `ParquetFile.iter_batches`, sehingga seluruh file tidak harus dimuat sekaligus. Conversion manifest mencatat fingerprint sumber dan hasil untuk mengenali cache yang masih sesuai.

`prepare_replay_month()` membaca **CSV** per chunk, memilih `tpep_pickup_datetime` dan `PULocationID`, membuang timestamp di luar bulan serta zona non-Manhattan, dan menulis replay CSV. Manifest replay memeriksa input, code, dan output sebelum hasil lama digunakan kembali.

## 2. Siapkan initial history

~~~powershell
uv run python scripts/prepare_historical_demand.py --start-date 2025-01-01 --end-date 2025-01-26
~~~

Setiap output mempunyai grid Manhattan zone × hour yang lengkap. Jam tanpa pickup mempunyai `trip_count=0`.

~~~text
data/processed/demand/2025-01-01.csv
...
data/processed/demand/2025-01-26.csv
~~~

Script menggunakan monthly replay CSV yang sama selama bulannya belum berganti. Initial history tidak harus merilis satu raw batch per hari terlebih dahulu.

## 3. Simulasikan batch baru

~~~powershell
uv run python scripts/simulate_daily_data.py --date 2025-01-27
uv run python scripts/prepare_daily_demand.py --date 2025-01-27
~~~

Hasil:

~~~text
data/raw/trips/2025-01-27.csv
data/processed/demand/2025-01-27.csv
~~~

Release membaca monthly CSV per chunk dan hanya menahan baris hari yang diminta di memori. Batch harian diurutkan berdasarkan pickup time.

Di Airflow, DAG `taxi_daily_replay` menjalankan release, validasi, aggregation, lalu penyiapan operational features. Parameter `replay_date` memilih tanggal, bukan tanggal wall clock laptop.

## 4. Buka file sebelum menjelaskan hasilnya

~~~powershell
Get-Content data/raw/trips/2025-01-27.csv -TotalCount 6
Get-Content data/processed/demand/2025-01-27.csv -TotalCount 6
~~~

Contoh struktur demand, dengan angka ilustrasi:

| timestamp | zone_id | zone | trip_count |
|---|---:|---|---:|
| 2025-01-27 00:00:00 | 161 | Midtown Center | 28 |

Satu baris demand berarti **satu zona pada satu jam**. Ini berbeda dari raw trips, yang mempunyai satu baris per perjalanan.

## 5. Features dan snapshot

Operational features:

~~~powershell
uv run python scripts/build_features.py --start-date 2025-01-01 --end-date 2025-01-27
Get-Content data/features/taxi_demand_features.csv -TotalCount 4
~~~

Training pipeline DVC menggunakan file features terpisah:

~~~powershell
uv run dvc repro create_training_snapshot
Get-Content data/snapshots/training/taxi_demand_2025-01-26.csv -TotalCount 4
~~~

Periode DVC mengikuti `params.json`. Snapshot berisi features dan `target_trip_count`; training script kemudian membaginya berdasarkan waktu. Dengan cutoff Jan 26 dan validation 5 hari, model belajar pada Jan 8–21 dan dievaluasi pada Jan 22–26. Jan 1–7 menyediakan history lag.

## Parsing CSV

CSV menyimpan tanggal sebagai teks. Helper `read_csv_dataset()` mengubahnya menjadi datetime sebelum operasi waktu. Float dibaca dengan `float_precision='round_trip'` agar nilai features tetap konsisten setelah serialisasi CSV.

Jangan mengubah timestamp/zona secara manual pada dataset pipeline untuk sekadar melihat isinya. Untuk latihan edit dan versioning gunakan `data/simple_case/data.csv`.

## Jika sudah mempunyai data Parquet dari versi lama

~~~powershell
uv run python scripts/migrate_data_to_csv.py --dry-run
uv run python scripts/migrate_data_to_csv.py
uv run dvc repro create_training_snapshot
~~~

Migrator mengonversi file lama dan memindahkan derived Parquet ke `data/legacy_parquet/<session>/`. Download TLC asli tetap disimpan. CSV derived yang sudah ada dipertahankan; migrator tidak menimpanya. Laporan migrasi disimpan di `data/experiments/csv-migration/`.

## Checkpoint

1. Apa perbedaan full source CSV, replay CSV, dan daily demand CSV?
2. Mengapa Parquet tetap ada di folder download?
3. Apa beda replay date dan tanggal laptop?
4. Mengapa timestamp perlu diparse saat membaca CSV?
5. Snapshot mempunyai target apa, dan kapan train/validation split dilakukan?

Lanjut ke [Feature Engineering](feature-engineering.md), [CSV Data Flow](csv-data-flow.md), dan [Airflow + DVC Hands-on](airflow-dvc-workshop.md).
