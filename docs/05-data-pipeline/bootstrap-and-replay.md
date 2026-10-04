# Data Bootstrap and Historical Replay

Sekarang kita mulai masuk ke bagian data pipeline. Sebelum Airflow ikut campur, flow-nya kita bikin jalan manual dulu supaya kelihatan jelas sebenarnya tiap step ngapain.

Flow yang kita punya sekarang:

```text
NYC TLC monthly data
        ↓
bootstrap
        ↓
replay source
        ↓
release one daily batch
        ↓
raw trip data
        ↓
aggregate hourly demand
```

Nanti Airflow tinggal orchestrate step-step yang memang sudah bisa jalan ini.

## Setup project

Dari root repository:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Kalau pakai Windows:

```powershell
.venv\Scripts\activate
pip install -e ".[dev]"
```

Project pakai Python 3.11 atau yang lebih baru.

## Bootstrap data

Jalankan:

```bash
python scripts/bootstrap_data.py
```

Secara default script akan nyiapin data January sampai March 2025.

Yang dilakukan script ini:

```text
download Yellow Taxi monthly parquet
        ↓
download Taxi Zone Lookup
        ↓
ambil pickup zone Manhattan
        ↓
buang timestamp di luar bulan yang seharusnya
        ↓
simpan compact replay source
```

File dari TLC yang full tetap disimpan di:

```text
data/source/tlc/
```

Sedangkan source yang sudah diringkas buat replay ada di:

```text
data/source/replay/
```

Taxi Zone Lookup ada di:

```text
data/metadata/
```

Semua generated data ini masuk `.gitignore`, jadi repository tetap ringan.

Kalau mau bootstrap bulan tertentu saja:

```bash
python scripts/bootstrap_data.py --months 2025-01
```

Kalau mau download dan prepare ulang:

```bash
python scripts/bootstrap_data.py --force
```

## Cek datanya dulu

Setelah bootstrap selesai, buka:

```text
notebooks/01-data-exploration.ipynb
```

Notebook ini sengaja simple. Kita cuma cek beberapa hal penting:

- berapa row yang masuk,
- berapa pickup zone yang tersedia,
- range timestamp,
- missing values,
- zone dengan pickup terbanyak,
- contoh hasil aggregation per jam.

Tujuannya supaya sebelum bikin model kita tahu data yang masuk itu memang masuk akal.

## Siapin initial training history

Sebelum production replay mulai, kita butuh history buat model pertama.

```bash
python scripts/prepare_historical_demand.py
```

Default-nya script ini nyiapin hourly demand dari 1 sampai 26 January 2025.

Setelah itu feature dataset bisa dibikin dengan:

```bash
python scripts/build_features.py
```

Detail feature-nya dibahas di [Feature Engineering](feature-engineering.md).

## Simulate new production data

Misalnya sekarang kita mau pura-pura tanggal production-nya adalah 27 January 2025:

```bash
python scripts/simulate_daily_data.py --date 2025-01-27
```

Output-nya:

```text
data/raw/trips/2025-01-27.parquet
```

Script hanya mengambil data untuk tanggal tersebut dari replay source.

Kalau command yang sama dijalankan lagi, file yang sudah ada akan di-skip. Kalau memang mau generate ulang:

```bash
python scripts/simulate_daily_data.py --date 2025-01-27 --force
```

Behavior ini bakal kepakai nanti waktu kita bahas idempotency di Airflow.

## Aggregate daily demand

Raw daily batch masih berbentuk trip-level data. Sekarang kita ubah menjadi demand per zone per jam:

```bash
python scripts/prepare_daily_demand.py --date 2025-01-27
```

Hasilnya:

```text
data/processed/demand/2025-01-27.parquet
```

Bentuk datanya kurang lebih:

```text
timestamp            zone_id    zone               trip_count
2025-01-27 08:00     161        Midtown Center     143
2025-01-27 08:00     162        Midtown East       121
2025-01-27 09:00     161        Midtown Center     158
...
```

Kita juga bikin complete zone-hour grid. Jadi kalau satu zone tidak punya pickup pada suatu jam, row-nya tetap ada dan `trip_count = 0`.

Ini penting karena untuk forecasting kita butuh time series yang konsisten, bukan cuma jam yang kebetulan punya trip.

## Folder roles

```text
data/
├── source/
│   ├── tlc/          full monthly file dari TLC
│   └── replay/       compact source buat historical replay
├── metadata/         taxi zone lookup
├── raw/
│   └── trips/        daily batch yang sudah "released"
├── processed/
│   └── demand/       hourly demand per zone
├── features/         nanti isi model-ready features
└── snapshots/        nanti dipakai untuk versioned training dataset
```

Bedanya `source` dan `raw` memang sengaja.

`source` itu data historical yang kita simpan di belakang layar buat simulator. `raw` adalah data yang dianggap sudah available ke production pipeline pada saat tertentu.

## Terus Airflow nanti ngapain?

Untuk sekarang kita masih jalanin manual:

```bash
python scripts/simulate_daily_data.py --date ...
python scripts/prepare_daily_demand.py --date ...
```

Nanti Airflow yang ngatur:

```text
release batch
    ↓
validate
    ↓
aggregate
    ↓
feature engineering
    ↓
prediction / evaluation
```

Jadi waktu masuk Airflow nanti kita nggak lagi bingung isi task-nya apa. Business logic-nya sudah ada, Airflow tinggal ngatur kapan dan urutannya.
