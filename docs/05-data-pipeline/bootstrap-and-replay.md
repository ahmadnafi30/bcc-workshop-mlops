# Data Pipeline Part 1 — Bootstrap and Historical Replay

## Kita mulai dari data source yang real

Core dataset kita datang dari NYC TLC Yellow Taxi Trip Records.

Kalau langsung pakai raw monthly file di setiap workshop step, prosesnya berat dan berulang-ulang. Jadi kita pecah data lifecycle-nya.

Mental model:

~~~text
official monthly source
        ↓
bootstrap
        ↓
compact replay source
        ↓
daily release
        ↓
processed hourly demand
~~~

Jadi bootstrap dan replay itu dua concern berbeda.

---

# Bootstrap: preparing the playground

Command:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Secara high-level, script ini:

1. download taxi zone lookup;
2. download monthly Yellow Taxi Parquet;
3. validate month;
4. select column yang kita butuh;
5. filter pickup zones ke Manhattan;
6. save compact replay source.

Kenapa kita bikin compact replay source?

Karena downstream pipeline nggak butuh seluruh original schema.

Semakin kecil data yang dibawa, semakin ringan workshop.

---

# Kenapa zone lookup penting?

PULocationID hanyalah angka.

Contoh:

~~~text
161
~~~

Tanpa metadata, kita nggak tahu itu Manhattan atau borough lain.

Zone lookup menghubungkan:

~~~text
LocationID
→ Borough
→ Zone
~~~

Sehingga kita bisa filter:

~~~text
Borough == Manhattan
~~~

---

# Kenapa raw dan replay source dipisah?

Folder:

~~~text
data/source/tlc
data/source/replay
~~~

Keduanya bukan duplicate tanpa alasan.

## tlc

Closer to original downloaded source.

## replay

Sudah workshop-friendly:

- relevant columns only,
- Manhattan only,
- month validated.

Jadi daily simulator baca replay, bukan raw source besar lagi.

---

# Initial historical demand

Sebelum production-like replay mulai, model perlu history.

Command:

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

Default:

~~~text
Jan 1–26
~~~

Kenapa range itu?

~~~text
Jan 1–7
warm-up

Jan 8–21
training

Jan 22–26
validation

Jan 27 onward
production replay
~~~

Timeline ini sengaja dibuat clean supaya peserta gampang membedakan initial model period dan post-training simulation period.

---

# Daily replay

Misalnya kita mau release Jan 27.

~~~bash
uv run python scripts/simulate_daily_data.py   --date 2025-01-27
~~~

Output:

~~~text
data/raw/trips/2025-01-27.parquet
~~~

Sekarang downstream pipeline berpikir:

> “Today’s available batch is Jan 27.”

Padahal kita sebenarnya baca historical data.

---

# Why this is useful

Workshop bisa mensimulasikan beberapa hari dalam waktu singkat.

~~~text
Jan 27
↓
Jan 28
↓
Jan 29
~~~

Tanpa harus menunggu real calendar.

Tapi chronological rule tetap dijaga.

---

# Validate before transform

Daily raw batch tidak langsung dipercaya.

Kita check hal seperti:

- file tidak kosong,
- timestamp parseable,
- row memang berasal dari requested date,
- pickup location tidak missing.

Kenapa validation step separate?

Karena bad input harus fail early.

~~~text
bad source
↓
validation fails
↓
STOP
~~~

Lebih baik daripada corruption baru ketahuan setelah model training.

---

# Aggregate raw trips

Raw daily batch:

~~~text
1 row = 1 trip
~~~

Kita aggregate jadi:

~~~text
1 row = 1 zone × 1 hour
~~~

Command manual:

~~~bash
uv run python scripts/prepare_daily_demand.py   --date 2025-01-27
~~~

Output:

~~~text
data/processed/demand/2025-01-27.parquet
~~~

---

# Zero demand is still data

Misalnya zone 161 jam 03:00 tidak punya trip.

Kalau hanya groupby trip yang exist, row itu tidak ada.

Tapi model perlu distinguish:

~~~text
missing
vs
zero
~~~

Makanya kita create full grid:

~~~text
24 hours × all Manhattan zones
~~~

dan fill missing count menjadi zero.

Ini bikin time series continuous.

---

# Folder lifecycle

Biar gampang:

~~~text
data/source
→ source artifacts

data/raw
→ released production-like batch

data/processed
→ cleaned / aggregated demand

data/features
→ model-ready feature table

data/snapshots
→ frozen training inputs

data/monitoring
→ predictions + evaluations
~~~

Folder structure kita reflect lifecycle, bukan random organization.

---

# Manual dulu, Airflow nanti

Kita sengaja punya scripts manual.

Kenapa?

Karena peserta harus ngerti logic:

~~~text
release
validate
aggregate
feature
~~~

sebelum lihat Airflow.

Kalau belum ngerti underlying step, Airflow graph hanya terlihat seperti kotak-kotak hijau.

---

# Checkpoint

Sebelum lanjut, kalian harus bisa jawab:

> Kenapa replay source berbeda dari raw daily batch?

Jawaban sederhananya:

~~~text
replay source
= historical pool

raw daily batch
= data yang "dirilis" untuk logical day tertentu
~~~

Kalau itu clear, orchestration nanti jauh lebih gampang dipahami.
