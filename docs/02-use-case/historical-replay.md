# Historical Replay — Simulating Production Without Waiting for Tomorrow

## Kenapa perlu replay?

Production data datang over time.

Misalnya real system hari ini tanggal Jan 27.

System belum punya Jan 28.

Besok baru Jan 28 muncul.

Itu natural.

Tapi workshop cuma beberapa jam.

Kita nggak mungkin:

> “Sekarang pipeline Jan 27 ya. Besok kita lanjut Jan 28.”

😄

Jadi kita punya historical data lengkap, tapi kita **reveal gradually** seolah-olah waktu berjalan.

Ini kita sebut historical replay.

---

# Analogi: recorded football match

Coba kalian punya full recording pertandingan.

Kalian sebenarnya sudah punya semua minute.

Tapi kalau mau simulate live commentator, kalian nggak langsung buka final score.

Kalian play:

~~~text
minute 1
minute 2
minute 3
...
~~~

Walaupun future ada di file recording, commentator hanya melihat information yang “sudah terjadi”.

Historical replay kita sama.

---

# Source replay

Bootstrap menghasilkan compact monthly replay file.

~~~text
data/source/replay/
├── yellow_tripdata_2025-01.parquet
├── yellow_tripdata_2025-02.parquet
└── ...
~~~

File itu sebenarnya punya whole month.

Tapi production simulator release satu date.

---

# Release Jan 27

Command manual:

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Output:

~~~text
data/raw/trips/2025-01-27.parquet
~~~

Sekarang downstream pipeline seolah-olah cuma menerima Jan 27 sebagai daily batch.

---

# Process daily demand

Setelah raw daily trip available:

~~~bash
uv run python scripts/prepare_daily_demand.py --date 2025-01-27
~~~

Output:

~~~text
data/processed/demand/2025-01-27.parquet
~~~

Sekarang bentuknya zone-hour demand.

---

# Initial history

Sebelum production replay dimulai, kita butuh training history.

Kita prepare:

~~~text
Jan 1–26
~~~

Kenapa sampai 26?

Karena initial lifecycle:

~~~text
Jan 1–7
warm-up

Jan 8–21
train

Jan 22–26
validation

Jan 27 onward
production-like replay
~~~

Jadi timeline-nya clean.

---

# Prediction timing

Misalnya target:

~~~text
Jan 28 18:00
~~~

Prediction harus dibuat menggunakan data sebelum 18:00.

~~~text
17:00
history latest known

↓ predict

18:00
target hour begins

18:00–18:59
trips happen

19:00-ish
18:00 ground truth complete
~~~

Baru setelah actual hour complete, kita bisa evaluate.

---

# “Tapi kan historical file sebenarnya sudah punya future data?”

Benar.

Itulah kenapa access pattern penting.

Source file boleh punya future.

Tapi online feature builder hanya membaca range:

~~~text
target - 168h
through
target - 1h
~~~

Jadi logic enforcement ada di serving code.

Historical replay bukan security boundary.

Dia teaching simulation buat chronological dependency.

---

# Idempotency

Kalau kita replay Jan 27 dua kali, apa yang harus terjadi?

Idealnya:

- nggak duplicate random rows,
- output predictable,
- repeated logical run safe.

Konsep ini disebut idempotency.

Dalam data pipeline, rerun itu normal.

Task bisa fail halfway.

Kita mungkin rerun.

Jadi pipeline sebaiknya dirancang supaya rerun tidak bikin data corrupt.

---

# Kenapa replay useful buat monitoring?

Karena kita bisa simulate:

~~~text
Day 1
prediction

Day 2
ground truth available
evaluate

Day 3
performance worsens
retrain
~~~

dalam waktu minutes.

Kita speed up the clock.

Tapi lifecycle dependency tetap mirip production.

---

# Apa yang fake dan apa yang real?

## Fake / simulated

~~~text
speed of time
~~~

Kita replay historical day lebih cepat.

## Real concept

~~~text
past-only features
delayed ground truth
separate daily batches
retraining based on evaluated predictions
~~~

Jadi workshop tetap ngajarin lifecycle yang transferable.

---

# Next step

Setelah ngerti replay, nanti Airflow akan mengambil manual flow:

~~~text
simulate_daily_data.py
↓
validate
↓
aggregate
↓
rebuild features
~~~

dan mengubahnya jadi observable DAG.

Itulah titik di mana orchestration mulai terasa useful.
