# Dataset — Dari Jutaan Taxi Trips Jadi Data yang Bisa Dipakai Model

Dataset utama kita berasal dari **NYC Taxi & Limousine Commission Yellow Taxi Trip Records**.

Ini official public trip data.

Tapi raw dataset punya jauh lebih banyak field daripada yang kita butuhkan.

Jadi ingestion kita deliberately selective.

---

## Field utama

Untuk demand counting, dua field paling penting:

~~~text
tpep_pickup_datetime
PULocationID
~~~

Kenapa cuma dua?

Karena target kita adalah:

> berapa banyak pickup terjadi di zone tertentu per jam.

Kita nggak butuh fare, tip, payment type, passenger count, dan field lain untuk core model.

Feature minimal yang relevan membuat pipeline lebih ringan dan konsep lebih jelas.

---

## Taxi Zone Lookup

PULocationID cuma numeric ID.

Supaya kita tahu ID itu Manhattan atau borough lain, kita pakai taxi zone lookup:

~~~text
LocationID
Borough
Zone
~~~

Flow:

~~~text
PULocationID
↓
join/lookup
↓
Borough
↓
filter Manhattan
~~~

---

## Kenapa base CloudFront URL AccessDenied?

Ini common confusion.

Kalau buka:

~~~text
https://d37ci6vzurychx.cloudfront.net/trip-data
~~~

bisa muncul:

~~~text
AccessDenied
~~~

Itu bukan berarti monthly file nggak bisa diakses.

CloudFront/S3 prefix tersebut tidak expose public directory listing.

Known object path tetap accessible.

Contoh:

~~~text
.../yellow_tripdata_2025-01.parquet
~~~

Analogi:

> Kalian tahu alamat rumah specific, tapi kompleksnya nggak kasih daftar semua penghuni.

Bootstrap script tahu exact object name, jadi download tetap works.

---

## Kenapa Parquet?

Parquet itu columnar format.

Kalau dataset punya banyak columns, kita bisa baca hanya yang dibutuhkan.

~~~text
read:
pickup_datetime
pickup_zone
~~~

tanpa load semua fare/payment columns.

Benefit:

- I/O lebih kecil,
- memory lebih kecil,
- type metadata lebih baik dibanding CSV,
- suitable buat analytics.

---

## Bootstrap flow

Command:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Behind the scenes:

~~~text
download zone lookup
↓
download monthly TLC parquet
↓
validate month
↓
read useful columns
↓
filter Manhattan
↓
drop invalid/out-of-month rows
↓
write compact replay parquet
~~~

---

## Kenapa source dan replay dipisah?

Kita punya:

~~~text
data/source/tlc/
data/source/replay/
~~~

### TLC source

Original downloaded monthly file.

### Replay source

Compact workshop-ready file setelah select useful columns + Manhattan filter.

Kenapa nggak overwrite source?

Karena source dan derived artifact punya responsibility berbeda.

Original source useful untuk:

- reprocessing,
- audit,
- experimenting with additional fields.

Replay source optimized buat hands-on.

---

## Data quality itu penting

Official data bukan berarti kita boleh blind trust.

Pipeline tetap check:

- expected columns,
- valid timestamp,
- month consistency,
- pickup location presence.

Kenapa?

External data schema bisa berubah.

Corrupted file bisa terjadi.

Dan bug ingestion jauh lebih murah ditangkap di awal daripada setelah model training.

Pattern sehat:

~~~text
ingest
↓
validate
↓
transform
~~~

---

## Optional weather feature

Weather bisa jadi useful external feature.

Taxi demand mungkin berubah saat:

- hujan,
- snow,
- temperature extreme,
- wind.

Tapi kita sengaja nggak include weather di core pipeline.

Kenapa?

Karena workshop already punya banyak lifecycle concept.

Weather berarti tambah:

- second data source,
- API/download logic,
- timestamp alignment,
- missing data,
- join strategy.

Itu bagus jadi extension setelah core lifecycle clear.

---

## Generated data nggak masuk Git

Folder data ada di repo sebagai structure, tapi generated files ignored.

Kenapa?

Git bukan tempat ideal buat repeatedly version large Parquet.

Kita track:

~~~text
code
config
pipeline definition
~~~

dan DVC bantu training data snapshot.

---

## Timezone caveat

TLC timestamp kita treat sebagai naive NYC local wall-clock time.

Kenapa?

Biar beginner workflow lebih simple.

Tapi production real harus lebih explicit tentang:

- timezone,
- UTC conversion,
- daylight saving time.

Workshop main period avoid DST transition, jadi simplification ini relatively safe untuk hands-on.

Yang penting: simplification-nya **disadari**, bukan accidentally ignored.

---

## Checkpoint

1. Kenapa cuma dua raw columns utama?
2. Taxi zone lookup dipakai buat apa?
3. Kenapa AccessDenied di folder URL bukan berarti file unavailable?
4. Kenapa source dan replay dipisah?
5. Kenapa external official data tetap perlu validation?
