# Data Pipeline — Feature Engineering: Dari Hourly Demand Jadi Model Matrix

Processed demand belum langsung ready buat model.

Kita perlu transform temporal history jadi numerical features.

Command:

~~~bash
uv run python scripts/build_features.py
~~~

Output:

~~~text
data/features/taxi_demand_features.parquet
~~~

---

## Input expectation

Input minimum:

~~~text
timestamp
zone_id
trip_count
~~~

Rows harus:

- timestamp valid,
- chronological,
- complete enough per zone.

---

## Step 1 — Sort

~~~text
zone_id
timestamp
~~~

Kenapa sorting first?

Shift/rolling rely on sequence.

Kalau row order random, lag jadi nonsense.

---

## Step 2 — Calendar features

From timestamp:

~~~text
hour
day_of_week
is_weekend
~~~

Tidak perlu historical demand buat ini.

Target time itself known at prediction time, jadi safe.

---

## Step 3 — Lag per zone

~~~text
group by zone
↓
shift 1,2,3,24,168
~~~

Per-zone grouping critical.

Kalau tidak, boundary antar zone contamination.

---

## Step 4 — Rolling

Kita shift history dulu.

Then rolling.

~~~text
previous demand
↓
rolling 3h
rolling 6h
rolling 24h
~~~

Kenapa shift first?

Prevent target leakage.

---

## Step 5 — Target

Target:

~~~text
target_trip_count
=
current hour demand
~~~

Feature lihat past.

Target adalah current.

---

## Step 6 — Drop incomplete warm-up

First week belum punya lag_168h.

Kalau model input butuh complete features, rows incomplete dropped.

Warm-up history tetap useful sebagai source lag.

---

## Batch vs online feature path

Training:

~~~text
batch dataframe
→ build many rows
~~~

Serving:

~~~text
one target request
→ look up history
→ build one feature row
~~~

Implementation path berbeda, semantics harus sama.

Ini training-serving consistency problem.

---

## Tests penting

Feature test seharusnya check exact expected value.

Contoh synthetic sequence:

~~~text
0,1,2,...,199
~~~

Untuk hour 168:

~~~text
lag_1h = 167
lag_24h = 144
lag_168h = 0
~~~

Kenapa synthetic useful?

Karena expected result bisa dihitung manual.

---

## Leakage test

Rolling 3h target 168 expected average dari:

~~~text
165
166
167
~~~

bukan include 168.

Kalau test dapat different, implementation suspicious.

---

## Feature schema contract

Model expected column order disimpan sebagai constant.

Kenapa?

DataFrame column order/type bisa matter.

Serving harus produce compatible input.

---

## Checkpoint

1. Sorting kenapa first?
2. Lag kenapa group by zone?
3. Rolling kenapa shift?
4. Warm-up rows kenapa drop?
5. Batch feature vs online feature beda implementation tapi harus sama semantics — kenapa?
