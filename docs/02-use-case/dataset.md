# Dataset: dari Taxi Trips ke CSV yang Bisa Dibaca

Workshop menggunakan **NYC TLC Yellow Taxi Trip Records**. Kita memprediksi jumlah pickup per zona Manhattan per jam.

## Format data yang digunakan

TLC menyediakan file bulanan dalam **Parquet**. Bootstrap menyimpan download asli, lalu langsung mengonversi **semua kolom** menjadi CSV. Setelah batas konversi ini, seluruh proses dataset menggunakan CSV.

| Lokasi | Isi | Format |
|---|---|---|
| `data/source/tlc/yellow_tripdata_2025-01.parquet` | Download asli dari TLC | Parquet, hanya arsip sumber download |
| `data/source/tlc/yellow_tripdata_2025-01.csv` | Hasil konversi seluruh kolom sumber | CSV |
| `data/source/replay/yellow_tripdata_2025-01.csv` | Pickup Manhattan yang valid, dua kolom utama | CSV |
| `data/raw/trips/2025-01-27.csv` | Batch trip untuk satu tanggal replay | CSV |
| `data/processed/demand/2025-01-27.csv` | Demand per zona dan jam | CSV |
| `data/features/taxi_demand_features.csv` | Features operasional | CSV |
| `data/snapshots/training/taxi_demand_2025-01-26.csv` | Input eksperimen sebelum train/validation split | CSV |

CSV dipilih agar peserta dapat melihat data langsung di editor atau Excel. File CSV bulanan lebih besar daripada Parquet yang dikompresi. Konversi dan filtering membaca batch 100.000 baris agar penggunaan memori tetap terkendali.

## Apa isi sumbernya?

Untuk menghitung demand, dua field utamanya:

| Field | Arti |
|---|---|
| `tpep_pickup_datetime` | Waktu pickup |
| `PULocationID` | ID zona pickup |

CSV hasil konversi TLC tetap menyimpan kolom sumber lain seperti fare dan passenger count. Replay source hanya menyimpan dua kolom yang diperlukan untuk use case ini.

## Taxi Zone Lookup

`data/metadata/taxi_zone_lookup.csv` memetakan `LocationID` ke `Borough` dan `Zone`. Lookup dipakai untuk memilih pickup Manhattan dan memberi nama zona pada tabel demand.

## Jalankan bootstrap

~~~powershell
uv run python scripts/bootstrap_data.py --months 2025-01
~~~

Alurnya:

~~~text
Download TLC Parquet + zone lookup
            ↓
Convert full monthly Parquet → CSV
            ↓
Read CSV in chunks
            ↓
Select pickup time + pickup zone
            ↓
Filter valid dates and Manhattan zones
            ↓
Write compact replay CSV
~~~

`--force` mengunduh ulang dan membangun kembali hasil bootstrap. Pada run biasa, file download dan konversi yang masih sesuai dapat digunakan kembali.

## Buka datanya

Untuk file bulanan, tampilkan sebagian baris agar tidak memuat seluruh CSV:

~~~powershell
uv run python -c "import pandas as pd; print(pd.read_csv('data/source/tlc/yellow_tripdata_2025-01.csv', nrows=5).to_string(index=False))"
~~~

Untuk preview replay yang lebih ringkas:

~~~powershell
Get-Content data/source/replay/yellow_tripdata_2025-01.csv -TotalCount 6
~~~

CSV dapat dibuka di Excel. Jika seluruh baris masuk satu kolom, gunakan import Text/CSV dengan delimiter comma. Untuk file bulanan yang lebih besar daripada batas baris aplikasi spreadsheet, gunakan preview `nrows` atau file harian yang lebih kecil.

## Kenapa URL TLC masih .parquet?

URL download mengikuti format yang disediakan TLC:

~~~text
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet
~~~

Jangan mengganti URL tersebut menjadi `.csv`. CSV dibuat lokal oleh bootstrap setelah download selesai. Buka object URL yang lengkap; base prefix CloudFront bukan halaman daftar file.

## Reproducibility

Git mencatat code dan metadata DVC. Output CSV pipeline tetap dikelola melalui DVC agar Git history tidak memuat dataset besar. Melihat CSV sebagai teks tidak menggantikan pencatatan hash, dependency, dan parameter.

Lanjut ke [Bootstrap & Replay](../05-data-pipeline/bootstrap-and-replay.md) dan [CSV Data Flow](../05-data-pipeline/csv-data-flow.md).
