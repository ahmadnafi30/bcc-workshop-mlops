# Step 1 — Data: Dari Official TLC File Sampai Hourly Demand

Sekarang environment sudah ready.

Kita mulai dari source paling bawah di lifecycle: **data**.

Goal step ini bukan sekadar download file.

Kita ingin ngerti:

~~~text
source data
↓
filtered replay source
↓
daily batch
↓
hourly demand
~~~

Kalau data layer nggak clear, tools di atasnya juga bakal confusing.

---

## Goal

Setelah step ini:

- official taxi data ter-download,
- zone lookup tersedia,
- replay source terbentuk,
- initial historical demand Jan 1–26 siap,
- kalian ngerti raw granularity vs model granularity.

---

## 1. Sebelum download, buka dataset docs

Raw TLC punya satu row per trip.

Coba jawab:

> “Kalau target kita jumlah pickup per zone per jam, apakah model perlu satu row per individual trip?”

No.

Kita akan aggregate.

Tapi raw source tetap penting sebagai starting point.

---

## 2. Bootstrap

~~~bash
uv run python scripts/bootstrap_data.py
~~~

First run bisa makan waktu.

Jangan panik kalau tidak instant.

### Behind the scenes

~~~text
download zone lookup
↓
download monthly Yellow Taxi parquet
↓
validate expected month
↓
select pickup time + pickup zone
↓
filter Manhattan
↓
write compact replay data
~~~

---

## 3. Inspect output

Lihat:

~~~text
data/source/tlc/
data/source/replay/
data/metadata/
~~~

Pertanyaan:

> “Kenapa original dan replay dipisah?”

Karena responsibility berbeda.

Original source = downloaded source.

Replay = smaller derived data optimized buat workshop lifecycle.

Kalau nanti preprocessing berubah, original source masih ada.

---

## 4. Open taxi zone lookup

Cari:

~~~text
data/metadata/taxi_zone_lookup.csv
~~~

Buka beberapa row.

Kalian akan lihat mapping:

~~~text
LocationID
Borough
Zone
~~~

Sekarang PULocationID numeric punya meaning.

---

## 5. Optional notebook

~~~bash
uv run jupyter lab
~~~

Open notebook exploration.

Jangan cuma run all.

Coba jawab:

- min timestamp?
- max timestamp?
- berapa Manhattan zone?
- ada missing?
- zone mana paling ramai?

Tujuan EDA ini bukan bikin 30 chart.

Tujuan EDA:

> “Apakah data yang masuk masuk akal?”

---

## 6. Prepare initial history

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

Output per day:

~~~text
data/processed/demand/2025-01-01.parquet
...
data/processed/demand/2025-01-26.parquet
~~~

---

## 7. Kenapa Jan 1–26?

Kita sengaja desain:

~~~text
Jan 1–7
→ warm-up history

Jan 8–21
→ training

Jan 22–26
→ validation
~~~

Longest lag = 168 hours = 7 days.

Tanpa warm-up, Jan 8 nggak punya lag one week.

---

## 8. Inspect satu processed day

Pakai Python cepat:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/processed/demand/2025-01-26.parquet'); print(df.head()); print(df.shape)"
~~~

Lihat columns.

Expected concept:

~~~text
timestamp
zone_id
trip_count
~~~

---

## 9. Zero-demand thought experiment

Misalnya zone 161 jam 03:00 nggak ada trip.

Kalau kita cuma group raw trip yang exist, row itu hilang.

Pertanyaan:

> “Hilang berarti missing data atau zero demand?”

Dalam problem kita: zero demand.

Makanya pipeline build complete zone-hour grid dan fill zero.

Ini small detail yang sangat penting.

---

## 10. Historical replay manual

Coba release Jan 27:

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Lalu:

~~~bash
uv run python scripts/prepare_daily_demand.py --date 2025-01-27
~~~

Sekarang kalian melakukan secara manual apa yang nanti Airflow orchestrate.

Ini deliberate.

Kita mau understand process sebelum automation.

---

## Mini challenge

Coba jawab:

1. Kalau CloudFront base folder AccessDenied, apakah monthly file pasti unavailable?
2. Kenapa source dan replay dipisah?
3. Kenapa model data granularity beda dari raw?
4. Kenapa zero-demand row harus dibuat?
5. Kenapa ada warm-up 7 hari?

---

## Checkpoint

Pastikan:

~~~text
data/processed/demand/2025-01-26.parquet
~~~

exists.

Next kita bikin model-ready features.
