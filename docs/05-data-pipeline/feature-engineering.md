# Data Pipeline Part 2 — Feature Engineering

## Dari hourly demand ke sesuatu yang bisa dimakan model

Processed demand kita punya tiga core column:

~~~text
timestamp
zone_id
trip_count
~~~

Model belum cukup hanya dengan itu.

Kita perlu encode temporal pattern.

Command:

~~~bash
uv run python scripts/build_features.py
~~~

Output:

~~~text
data/features/taxi_demand_features.parquet
~~~

---

# Step 1 — Combine processed history

Feature builder baca daily demand history.

Kenapa perlu combine multiple days?

Karena feature terjauh kita:

~~~text
lag_168h
~~~

yang berarti satu minggu ke belakang.

Jadi per-day computation harus tetap punya akses historical context.

---

# Step 2 — Sort correctly

Sebelum shift atau rolling:

~~~text
sort by
zone_id
timestamp
~~~

Kenapa?

Time-based operation depend on order.

Kalau row random, shift satu row tidak berarti previous hour.

Ini kelihatan sepele, tapi silent bug seperti ini bahaya karena code tetap jalan.

---

# Step 3 — Calendar features

Dari timestamp:

~~~text
hour
day_of_week
is_weekend
~~~

Calendar features aman dipakai karena target timestamp diketahui saat prediction.

Kalau kita predict:

~~~text
2025-01-28 18:00
~~~

kita already tahu:

- hour = 18,
- weekday apa,
- weekend atau nggak.

---

# Step 4 — Lag features

Per zone:

~~~text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
~~~

Per zone itu keyword penting.

Kalau groupby zone tidak dilakukan, historical value zone lain bisa bocor.

Jadi pattern:

~~~text
groupby(zone_id)
↓
shift(...)
~~~

---

# Step 5 — Rolling features

Kita pakai:

~~~text
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Important implementation:

~~~text
shift(1)
↓
rolling(...)
~~~

Kenapa shift dulu?

Karena current row adalah target.

Kalau rolling include current trip_count, target bocor.

Untuk target 18:00:

~~~text
valid 3h window:
15:00
16:00
17:00
~~~

bukan:

~~~text
16:00
17:00
18:00 actual
~~~

---

# Step 6 — Define target

Current:

~~~text
trip_count
~~~

menjadi:

~~~text
target_trip_count
~~~

Jadi feature row punya historical inputs + target current.

---

# Step 7 — Drop incomplete rows

Early history belum punya full lag.

Misalnya Jan 2 belum punya lag_168h.

Row seperti itu incomplete untuk model.

Mereka tidak masuk final model-ready dataset.

Tapi historical source tetap berguna buat support future lags.

---

# Feature schema contract

Model kita expect column tertentu:

~~~text
zone_id
hour
day_of_week
is_weekend
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Urutan dan semantics harus consistent.

---

# Batch vs online features

Training uses batch feature builder.

Serving uses online feature builder untuk satu request.

Implementation beda, meaning harus sama.

Contoh:

~~~text
lag_24h in training
must mean exactly same thing
as lag_24h in serving
~~~

Kalau nggak, kita punya training-serving skew.

---

# Test semantics, not just execution

Feature pipeline punya automated tests.

Kenapa?

Karena leakage bug tidak selalu crash.

Contoh bug:

~~~text
rolling includes target
~~~

Code jalan.

Metric mungkin malah terlihat luar biasa.

Justru itu berbahaya.

Test synthetic sequence membantu verify exact values.

---

# Example synthetic test

Misalnya trip_count:

~~~text
0
1
2
3
...
~~~

Untuk hour 168:

~~~text
lag_168h = 0
lag_1h = 167
~~~

Expected values gampang dihitung.

Kalau result beda, logic salah.

---

# Rebuild after each replay

Jan 27 masuk.

~~~text
processed demand extends
↓
rebuild features
~~~

Jan 28 masuk.

~~~text
rebuild again
~~~

Feature file represent latest available state.

Kalau mau train reproducibly, kita tidak langsung rely on mutable latest file.

Kita freeze snapshot lewat DVC.

---

# Checkpoint

Sebelum lanjut, kalian harus bisa explain:

> Kenapa rolling mean dibuat setelah shift?

Kalau jawabannya:

> “Supaya current target tidak ikut masuk historical feature.”

berarti leakage concept sudah masuk.
