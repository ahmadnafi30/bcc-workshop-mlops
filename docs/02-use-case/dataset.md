# Dataset — NYC Yellow Taxi Trip Records

## Data source utama

Core dataset workshop ini adalah **NYC Taxi & Limousine Commission Yellow Taxi Trip Records**.

Kita pakai data trip yang memang berasal dari operasi taxi di New York City.

Raw file-nya punya banyak kolom, tapi buat use case demand forecasting kita sebenarnya hanya butuh sebagian kecil.

Field paling penting:

~~~text
tpep_pickup_datetime
PULocationID
~~~

Dan dari Taxi Zone Lookup:

~~~text
LocationID
Borough
Zone
~~~

---

# Apa arti field-field itu?

## tpep_pickup_datetime

Waktu pickup taxi terjadi.

Contoh:

~~~text
2025-01-14 08:37:21
~~~

## PULocationID

Pickup Location ID.

Ini integer yang menunjuk taxi zone.

Contoh:

~~~text
161
~~~

Tapi angka 161 sendiri kurang meaningful buat manusia.

Makanya kita punya zone lookup.

## Taxi Zone Lookup

Lookup mengubah:

~~~text
LocationID = 161
~~~

menjadi informasi seperti borough dan zone name.

Kita pakai lookup terutama buat filter:

~~~text
Borough == Manhattan
~~~

---

# Kenapa tidak pakai semua kolom?

Raw Yellow Taxi data punya banyak informasi lain.

Misalnya fare, payment, passenger count, dropoff location, dsb.

Tapi target kita adalah **pickup demand**.

Kalau tujuan kita cuma count pickup per zone-hour, cukup:

~~~text
pickup time
pickup zone
~~~

Lebih sedikit column berarti:

- read lebih cepat,
- memory lebih kecil,
- logic lebih gampang dijelaskan.

Ini juga lesson penting:

> More columns tidak selalu berarti better pipeline.

Ambil yang memang relevant.

---

# Kenapa Parquet?

Monthly TLC data disimpan dalam Parquet.

Parquet adalah columnar format.

Secara simplified, kalau kita cuma butuh dua column:

~~~text
pickup datetime
pickup location
~~~

reader bisa fokus ke column itu tanpa harus parse seluruh row structure seperti format text biasa.

Keuntungan:

- lebih efficient buat analytical data,
- type information lebih baik,
- cocok dengan Pandas/PyArrow.

---

# Base URL kok AccessDenied?

Ini sempat membingungkan juga kalau baru pertama lihat.

Kalau buka:

~~~text
https://d37ci6vzurychx.cloudfront.net/trip-data
~~~

bisa keluar XML:

~~~text
AccessDenied
~~~

Apakah dataset-nya unavailable?

No.

Yang tidak diizinkan adalah **directory listing**.

CloudFront/S3-like object storage tidak harus menyediakan halaman “isi folder”.

Tapi kalau kita tahu exact object key:

~~~text
yellow_tripdata_2025-01.parquet
~~~

file-nya bisa diakses.

Mental model-nya:

~~~text
"Lihat isi folder?"
❌

"Ambil file exact ini?"
✅
~~~

Code kita build URL object exact berdasarkan month.

---

# Bootstrap stage

Command:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Secara high-level:

~~~text
download zone lookup
        ↓
download monthly Yellow Taxi parquet
        ↓
select relevant columns
        ↓
filter Manhattan zones
        ↓
validate timestamps
        ↓
save compact replay source
~~~

---

# Folder data kita

Setelah bootstrap:

~~~text
data/
├── metadata/
│   └── taxi_zone_lookup.csv
│
└── source/
    ├── tlc/
    │   └── original monthly parquet
    │
    └── replay/
        └── compact filtered parquet
~~~

Kenapa source dan replay dipisah?

Karena purpose-nya beda.

## source/tlc

Closer to official downloaded artifact.

## source/replay

Workshop-optimized version.

Kita sudah:

- reduce columns,
- filter Manhattan,
- validate month.

Jadi subsequent simulation lebih ringan.

---

# Kenapa kita pakai historical replay?

Karena MLOps pipeline production biasanya menerima data over time.

Tapi workshop cuma beberapa jam.

Kita nggak mungkin bilang:

> “Oke peers, sekarang tunggu besok dulu ya buat dapat batch baru.”

😄

Jadi historical data kita perlakukan seolah-olah datang gradually.

Misalnya:

~~~text
initial history
Jan 1–26

then replay
Jan 27
Jan 28
Jan 29
...
~~~

Kita percepat waktu, bukan mengubah dependency.

---

# Data granularity berubah

Ini penting banget.

Raw:

~~~text
1 row = 1 trip
~~~

Processed:

~~~text
1 row = 1 taxi zone × 1 hour
~~~

Contoh raw:

| pickup datetime | zone |
| --- | ---: |
| 17:02 | 161 |
| 17:14 | 161 |
| 17:58 | 161 |

Processed:

| hour | zone | trip_count |
| --- | ---: | ---: |
| 17:00 | 161 | 3 |

---

# Bagaimana kalau suatu zone nggak punya trip?

Ini tricky.

Kalau groupby hanya berdasarkan trip yang ada, combination:

~~~text
zone 161
03:00
0 trips
~~~

tidak muncul sama sekali.

Padahal:

~~~text
missing row
≠
zero demand
~~~

Untuk time series, zero demand adalah valid observation.

Jadi kita bikin complete grid:

~~~text
all Manhattan zones
×
24 hours
~~~

Lalu missing counts kita fill:

~~~text
trip_count = 0
~~~

Sekarang tiap zone punya continuous hourly history.

---

# Optional weather enrichment

Kalau nanti mau bikin modeling lebih interesting, taxi demand bisa dikombinasikan dengan weather.

Contoh:

~~~text
temperature
rainfall
snowfall
wind_speed
~~~

Kenapa weather potentially useful?

Karena weather bisa affect transportation behavior.

Tapi di workshop:

> Weather bukan core dependency.

Core pipeline harus tetap bisa jalan hanya dengan TLC.

Kenapa kita pilih begitu?

Supaya fokus workshop tetap MLOps, bukan habis waktu di external weather API integration.

---

# Timezone note

Untuk workshop, timestamp TLC diperlakukan sebagai naive NYC local wall-clock time.

Artinya kita tidak memasang timezone-aware transformation di setiap stage.

Ini simplification.

Kenapa masih acceptable buat core walkthrough?

Karena main training/replay awal ada sekitar January–February, sebelum DST transition March.

Kalau project mau dibawa lebih jauh sampai March dan seterusnya, DST handling harus didesign lebih explicit.

Ini contoh penting:

> Workshop simplification harus diketahui, bukan disembunyikan.

---

# Data tidak di-commit ke Git

Generated data di-ignore.

Kenapa?

Monthly taxi parquet besar.

Git bukan tool ideal untuk menyimpan history binary dataset besar.

Git tetap track:

- code,
- pipeline definitions,
- docs.

DVC bantu training snapshot reproducibility.

Jadi responsibility-nya clean.
