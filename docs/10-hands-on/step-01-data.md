# Step 1 — Data: Dari Official Taxi Records ke Hourly Demand

Oke, environment sudah aman.

Sekarang baru kita masuk data.

Di step ini jangan buru-buru mikirin model.

Target kita adalah ngerti:

> “Data apa yang sebenarnya kita punya, dan bentuk apa yang dibutuhkan model nanti?”

---

# Target step

Setelah selesai:

~~~text
official TLC data
↓
compact replay source
↓
initial daily processed demand
~~~

Kalian juga harus ngerti kenapa raw trip data perlu diubah jadi zone-hour demand.

---

# 1. Bootstrap official data

Run:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

First run bisa cukup lama karena monthly Parquet file besar.

Jangan panik kalau belum instant.

---

# Apa yang sedang dilakukan?

Secara concept:

~~~text
Taxi Zone Lookup
        +
Yellow Taxi Monthly Parquet
        ↓
select useful columns
        ↓
filter Manhattan
        ↓
validate month
        ↓
save replay source
~~~

Kita nggak hanya download file.

Kita prepare source buat repeated simulation.

---

# 2. Inspect folder

Setelah selesai:

~~~text
data/source/tlc/
data/source/replay/
data/metadata/
~~~

Coba lihat file sizes.

Biasanya replay source lebih compact daripada original source.

Kenapa?

Karena kita drop unrelated columns dan filter Manhattan.

---

# 3. Coba buka zone lookup

File:

~~~text
data/metadata/taxi_zone_lookup.csv
~~~

Lihat beberapa row.

Cari:

~~~text
LocationID
Borough
Zone
~~~

Sekarang angka PULocationID mulai punya context.

---

# 4. Kenapa CloudFront base URL AccessDenied?

Kalau penasaran dan buka directory URL, mungkin keluar AccessDenied.

Jangan langsung assume bootstrap broken.

Storage endpoint tidak menyediakan directory listing.

Script tahu exact object path.

Ini normal.

---

# 5. Optional EDA notebook

Start Jupyter:

~~~bash
uv run jupyter lab
~~~

Open:

~~~text
notebooks/01-data-exploration.ipynb
~~~

Jangan sekadar Run All.

Coba jawab:

### Berapa row?

### Time range-nya apa?

### Berapa Manhattan zones?

### Ada missing pickup location?

### Top pickup zones apa?

Tujuan EDA di workshop:

> Sanity check data source sebelum pipeline lebih jauh.

Bukan bikin full analytics report.

---

# 6. Prepare historical demand

Run:

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

Default prepare Jan 1–26.

Output per day:

~~~text
data/processed/demand/
├── 2025-01-01.parquet
├── 2025-01-02.parquet
...
└── 2025-01-26.parquet
~~~

---

# 7. Coba inspect satu file

Pakai Python:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/processed/demand/2025-01-26.parquet'); print(df.head()); print(df.shape)"
~~~

Kalian harus lihat column roughly:

~~~text
timestamp
zone_id
trip_count
~~~

---

# Coba pikirkan shape-nya

Kalau Manhattan punya N zones, satu day ideal row count:

~~~text
24 × N
~~~

Kenapa 24?

Karena kita explicitly create every hour.

Kalau actual trip 0, row tetap ada.

---

# Mini challenge: missing vs zero

Coba jawab:

> Zone A jam 03:00 nggak punya pickup. Apakah kita harus hapus row atau set trip_count=0?

Jawab:

~~~text
trip_count = 0
~~~

Karena no pickup adalah actual observation.

Missing row bisa berarti data unavailable.

Semantics beda.

---

# 8. Understand timeline

Initial data:

~~~text
Jan 1–7
warm-up

Jan 8–21
training-ready

Jan 22–26
validation period
~~~

Jan 27 belum diproses sebagai initial history karena nanti kita pakai buat production replay.

Jadi data split bukan random.

Timeline sengaja punya meaning.

---

# 9. Manual replay Jan 27

Sekarang kita coba “data baru datang”.

~~~bash
uv run python scripts/simulate_daily_data.py   --date 2025-01-27
~~~

Output:

~~~text
data/raw/trips/2025-01-27.parquet
~~~

Lanjut process:

~~~bash
uv run python scripts/prepare_daily_demand.py   --date 2025-01-27
~~~

Output:

~~~text
data/processed/demand/2025-01-27.parquet
~~~

Nanti Airflow akan automate flow ini.

---

# What just happened?

Historical month sebenarnya sudah kita punya.

Tapi kita hanya release satu day.

Jadi kita simulate:

~~~text
"Today Jan 27 data arrived."
~~~

Ini historical replay.

---

# Common issues

## Download lambat

Official monthly data memang besar.

Presenter sebaiknya punya pre-downloaded backup.

## Parquet memory issue

Replay source sudah compact, tapi original monthly source tetap cukup besar.

Close notebook/process yang unnecessary.

## File date mismatch

Daily preparation validates requested date.

Jangan rename file asal tanpa memahami contents.

---

# Checkpoint

Sebelum lanjut, kalian harus bisa explain:

~~~text
official monthly source
vs
replay source
vs
raw daily batch
vs
processed demand
~~~

Kalau empat stage ini clear, feature engineering berikutnya akan lebih natural.
