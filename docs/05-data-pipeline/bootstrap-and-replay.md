# Data Pipeline — Bootstrap & Replay: Dari Official TLC Data Sampai Batch yang Siap Diproses

Sekarang kita masuk ke implementation layer dari historical replay.

Di concept page sebelumnya kita bahas **kenapa** replay diperlukan.

Di halaman ini kita fokus:

> “Actual data bergerak lewat folder dan function apa saja?”

Goal-nya bukan cuma hafal command bootstrap_data.py.

Kita ingin ngerti boundaries.

---

# Full journey satu batch data

Coba lihat perjalanan besarnya:

~~~text
Official NYC TLC monthly Parquet
        ↓
download
        ↓
data/source/tlc
        ↓
select useful columns
filter Manhattan
validate month
        ↓
data/source/replay
        ↓
release one logical date
        ↓
data/raw/trips/YYYY-MM-DD.parquet
        ↓
validate daily batch
        ↓
aggregate zone × hour
        ↓
data/processed/demand/YYYY-MM-DD.parquet
~~~

Setiap arrow punya reason.

Kalau kalian ngerti reason-nya, folder structure nggak lagi kelihatan sebagai “banyak banget file”.

---

# Phase 1 — Bootstrap official source

Command:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Bootstrap download dua tipe source.

## Taxi trip data

Monthly Parquet Yellow Taxi.

## Taxi zone lookup

Metadata mapping:

~~~text
LocationID
→ Borough
→ Zone
~~~

Tanpa lookup, PULocationID cuma angka ID.

Kita nggak tahu ID itu Manhattan, Queens, Bronx, atau area mana.

---

# Kenapa source official disimpan dulu?

Kita bisa saja:

~~~text
download
↓
filter
↓
delete original
~~~

Tapi workshop sengaja preserve source download locally.

Benefit:

- preprocessing bisa diulang tanpa download ulang;
- debugging lebih gampang;
- replay preparation bisa berubah;
- workshop lebih tahan internet problem setelah initial bootstrap.

Ini simple form of raw-source preservation.

Production data lake sering punya principle serupa:

> jangan buru-buru kehilangan source yang belum ditransform.

---

# Phase 2 — Compact replay preparation

Official monthly Yellow Taxi punya banyak columns.

Core use case kita terutama butuh:

~~~text
tpep_pickup_datetime
PULocationID
~~~

Kita juga hanya fokus Manhattan.

Jadi replay preparation melakukan:

~~~text
read selected columns
↓
validate timestamp month
↓
filter Manhattan LocationID
↓
save compact Parquet
~~~

---

# Kenapa select columns dulu?

Kalau source punya banyak field seperti fare, payment type, passenger count, vendor, toll, dan lain-lain, sementara kita cuma perlu pickup time + location, membaca semua columns berulang itu wasteful.

Parquet memungkinkan column pruning.

Jadi kita bisa bilang:

> “Saya cuma butuh dua column ini.”

Lebih efisien memory dan I/O.

---

# Kenapa validate month?

Misalnya file bernama:

~~~text
yellow_tripdata_2025-01.parquet
~~~

Kita expect timestamp January.

Tapi external dataset bisa punya row anomali.

Kalau ada February timestamp dan kita blindly masukkan ke replay January:

~~~text
January replay
↓
future February row
↓
daily filter / history
↓
temporal assumption bocor
~~~

Validation month membantu menjaga replay source tetap clean secara time boundary.

---

# Phase 3 — Metadata zone lookup

Zone lookup disimpan:

~~~text
data/metadata/taxi_zone_lookup.csv
~~~

Kenapa lookup dipisah dari trip data?

Karena dia reference metadata.

Trip row punya:

~~~text
PULocationID = 161
~~~

Lookup memberi:

~~~text
161
→ Manhattan
→ Midtown Center
~~~

Kita filter Manhattan berdasarkan mapping ini.

Ini contoh sederhana relational thinking:

~~~text
fact/event data
+
reference dimension
~~~

---

# Kenapa replay source bukan raw production batch?

Ini distinction penting.

~~~text
data/source/replay/yellow_tripdata_2025-01.parquet
~~~

masih berisi satu bulan historical recording.

Sedangkan:

~~~text
data/raw/trips/2025-01-27.parquet
~~~

adalah satu batch yang sudah logically released.

Jadi:

~~~text
replay source
→ simulation reservoir

raw daily
→ production-facing input boundary
~~~

Kalau kalian campur dua role ini, replay logic jadi sulit dijelaskan.

---

# Phase 4 — Release one logical day

Command:

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Under the hood:

~~~text
target date
↓
resolve source month
↓
read replay source
↓
select exact date
↓
write raw daily batch
~~~

Output:

~~~text
data/raw/trips/2025-01-27.parquet
~~~

Downstream sekarang nggak perlu tahu satu bulan full tersedia.

Dia hanya tahu batch Jan 27 sudah datang.

---

# Kenapa output per day?

Partition per-day memberi banyak benefit.

## Replay gampang

~~~text
Jan 27
Jan 28
Jan 29
~~~

## Validation gampang

Semua timestamp file Jan 27 seharusnya Jan 27.

## Monitoring gampang

Ground truth target date bisa resolve file yang jelas.

## Retry gampang

Satu logical date punya deterministic output path.

## Debugging gampang

Kalau Jan 28 aneh, inspect Jan 28 tanpa scan seluruh quarter.

Production object storage/data warehouse sering pakai partitioning karena reason serupa.

---

# Phase 5 — Validation sebelum transformation

Daily batch jangan langsung diaggregate.

Kita validate hal basic:

- file ada;
- tidak empty;
- required columns ada;
- timestamp parseable;
- timestamp date match requested date;
- pickup location available.

Kenapa check date?

Bayangin requested Jan 27 tapi file somehow berisi Jan 28.

Kalau lanjut:

~~~text
future event
↓
processed history
↓
lag/rolling feature
↓
model sees future
~~~

Data quality issue berubah jadi leakage issue.

---

# Fail early vs silent correction

Suppose required column missing.

Option A:

~~~text
silently fill default
↓
continue
~~~

Option B:

~~~text
raise validation error
↓
stop downstream
~~~

Workshop prefer B.

Visible failure biasanya jauh lebih aman daripada silent corruption.

Kalau pipeline merah, kita tahu ada masalah.

Kalau pipeline hijau tapi data salah, itu lebih berbahaya.

---

# Phase 6 — Aggregate raw trip ke hourly demand

Manual command:

~~~bash
uv run python scripts/prepare_daily_demand.py --date 2025-01-27
~~~

Concept:

~~~text
trip rows
↓
group by hour + zone
↓
complete zone-hour grid
↓
fill zero demand
↓
processed demand
~~~

Output:

~~~text
data/processed/demand/2025-01-27.parquet
~~~

---

# Complete grid — kenapa row zero harus dibuat?

Bayangin Manhattan punya N zones.

Satu hari punya 24 hours.

Ideal shape:

~~~text
N × 24 rows
~~~

Kalau satu combination nggak ada trip, trip_count harus zero.

Tanpa complete grid:

~~~text
03:00 zone 161
→ row hilang
~~~

Lalu lag/rolling time series punya hole.

Jadi zero demand bukan missing data.

Ini domain semantics.

---

# Sanity check sederhana setelah aggregation

Kalian bisa inspect:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/processed/demand/2025-01-27.parquet'); print(df.shape); print(df.head())"
~~~

Pertanyaan:

- zone count masuk akal?
- setiap zone punya 24 hours?
- trip_count non-negative?
- total pickups roughly sesuai raw trip count?

Simple invariants bisa catch banyak bug.

---

# Initial historical demand

Command:

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

Ini prepare Jan 1–26.

Kenapa special script?

Karena kita perlu initial state sebelum production-like replay.

Kalau harus replay 26 hari manual satu-satu, teaching time habis.

Output semantics tetap sama:

~~~text
processed hourly demand per date
~~~

Jadi kita optimize onboarding, bukan mengubah model logic.

---

# Apa yang nanti Airflow orchestrate?

Daily DAG call reusable logic:

~~~text
release_replay_batch
↓
validate_replay_batch
↓
prepare_replay_demand
↓
rebuild_replay_features
~~~

Notice nama function hampir sama dengan business step.

Ini bagus buat readability.

Saat lihat Graph Airflow, participant bisa relate ke manual flow.

---

# Kenapa script dan src function dua-duanya ada?

### scripts

Human-friendly CLI entry point.

Contoh:

~~~text
simulate_daily_data.py
~~~

### src

Reusable logic.

Contoh:

~~~text
release_daily_batch
~~~

Benefit:

~~~text
manual CLI
→ reuse src

Airflow
→ reuse src

tests
→ call src
~~~

Satu domain implementation dipakai banyak interface.

Kalau business logic hanya hidup di script, Airflow sering akhirnya copy-paste code.

---

# Idempotency detail

Output path deterministic:

~~~text
data/raw/trips/<date>.parquet
data/processed/demand/<date>.parquet
~~~

Pattern ini membantu rerun.

Production idempotency bisa lebih kompleks:

- transaction;
- partition overwrite;
- deduplication key;
- checkpoint;
- exactly-once-ish semantics.

Workshop memberi intuition dasar:

> same logical date should not create random duplicate state.

---

# Download reliability

Network download bisa gagal.

Potential issue:

- timeout;
- connection drop;
- partial file;
- disk space;
- remote unavailable.

Downloader project pakai temporary partial file sebelum final destination.

Kenapa?

Bayangin kita langsung write:

~~~text
yellow_tripdata_2025-01.parquet
~~~

Network putus 40%.

File tetap ada.

Next run mungkin lihat:

> “File sudah ada, skip.”

Sekarang corrupted partial file dianggap complete.

Dengan temp pattern:

~~~text
download.part
↓ success
rename final
~~~

Final filename hanya muncul setelah download complete.

Ini reliability pattern yang kecil tapi professional.

---

# Base CloudFront AccessDenied

Kalau buka:

~~~text
https://d37ci6vzurychx.cloudfront.net/trip-data
~~~

dan dapat AccessDenied, jangan panic.

Object storage tidak expose directory listing.

Exact object:

~~~text
.../yellow_tripdata_2025-01.parquet
~~~

tetap bisa diakses.

Mental model:

~~~text
browse folder
❌

request exact known object
✅
~~~

---

# External data tetap perlu distrust sehat

“Official source” bukan berarti:

> “Pasti sempurna, nggak usah validate.”

External system bisa berubah.

Schema bisa berubah.

Row anomali bisa ada.

Network bisa corrupt transfer.

Healthy data engineering principle:

> trust, but validate the assumptions your model depends on.

---

# Data issue atau model issue?

Suppose MAE mendadak naik.

Data scientist instinct kadang:

> “Tune model.”

Tapi bisa saja:

- processed file duplicate;
- zone lookup salah;
- date leakage;
- missing hours;
- raw batch incomplete.

Sebelum tune model, inspect data pipeline.

MLOps membuat hubungan data → model lebih visible, tapi diagnosis tetap butuh reasoning.

---

# Debugging by artifact layer

## Download fail

Check network, URL, partial file, disk.

## Replay source missing

Bootstrap belum selesai.

## Daily raw empty

Check target date dan Manhattan filter.

## Validation fail

Read exact schema/date error.

## Processed row count wrong

Check aggregation + complete grid.

## Features wrong

Jangan kembali download dulu. Debug next layer.

Selalu narrow layer.

---

# Mini exercise: trace Jan 27

Coba tanpa lihat diagram tulis:

~~~text
official monthly file
→ ?
→ ?
→ ?
→ processed demand
~~~

Expected:

~~~text
official TLC
→ source/tlc
→ source/replay
→ raw/trips/Jan27
→ processed/demand/Jan27
~~~

Kalau chain ini clear, data layer sudah mulai kebayang sebagai system, bukan kumpulan Parquet.

---

# Checkpoint

1. Kenapa official source disimpan dulu?
2. Replay source beda apa dengan TLC source?
3. Kenapa replay source compact?
4. Zone lookup role-nya apa?
5. Kenapa raw output partition per day?
6. Validation sebelum aggregation solve apa?
7. Wrong date bisa jadi leakage bagaimana?
8. Complete grid kenapa perlu?
9. Initial historical script kenapa ada?
10. scripts dan src beda responsibility apa?
11. Idempotency membantu retry bagaimana?
12. Temporary partial download solve failure mode apa?
13. AccessDenied base folder artinya dataset unavailable nggak?
14. Kalau MAE naik, kenapa model belum tentu root cause?

Kalau semua clear, next kita masuk feature engineering dan lihat gimana hourly demand berubah jadi model matrix tanpa leakage.
