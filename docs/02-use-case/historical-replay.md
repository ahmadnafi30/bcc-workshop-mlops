# Historical Replay — Gimana Demo Production Lifecycle Pakai Data Masa Lalu?

Production system menerima data over time.

Workshop kita pakai historical data yang sebenarnya sudah lengkap.

Problemnya:

Kalau kita langsung kasih semua future data ke pipeline, simulation jadi nggak realistic.

Model bisa accidentally lihat masa depan.

Historical replay solve itu.

---

## Analogi pertandingan rekaman

Kalian punya full recording pertandingan sepak bola.

Skor akhir sudah tersimpan di video.

Tapi kalau mau latihan jadi live commentator, kalian nggak langsung lompat menit 90.

Kalian play:

~~~text
minute 1
minute 2
minute 3
...
~~~

Data future sebenarnya ada di disk, tapi kalian **reveal gradually**.

Itu replay.

---

## Replay Source

Bootstrap prepare monthly compact data:

~~~text
data/source/replay/
~~~

Ini recording penuh.

Tapi daily pipeline tidak langsung consume semua.

Kita release per date.

---

## Simulate Jan 27

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Output:

~~~text
data/raw/trips/2025-01-27.parquet
~~~

Sekarang downstream pipeline behave seolah Jan 27 baru datang.

---

## Aggregate ke hourly demand

Daily raw trip batch:

~~~text
many taxi trips
~~~

jadi:

~~~text
zone × hour demand
~~~

Output:

~~~text
data/processed/demand/2025-01-27.parquet
~~~

---

## Initial history

Kenapa kita sudah prepare Jan 1–26 sebelum replay?

Karena kita butuh:

~~~text
Jan 1–7
→ lag warm-up

Jan 8–21
→ initial training

Jan 22–26
→ validation
~~~

Lalu “production simulation” mulai Jan 27.

---

## Prediction timing

Target:

~~~text
Jan 28 18:00
~~~

Prediction ideally dibuat sebelum actual 18:00 known.

Serving feature provider restrict history sampai:

~~~text
17:00
~~~

Walaupun file full Jan 28 mungkin eventually ada, logic enforce past-only input.

---

## Ground truth delayed

Setelah 18:00 period lewat, actual demand available.

Sekarang kita bisa evaluate:

~~~text
prediction 147
actual 160
absolute error 13
~~~

Inilah basis model monitoring.

---

## Replay mempercepat waktu, bukan menghapus causality

Workshop bisa simulate beberapa hari dalam 20 menit.

Apakah itu fake?

Clock speed-nya simulated.

Tapi dependency logic tetap:

~~~text
data release
↓
prediction
↓
ground truth
↓
evaluation
↓
retraining decision
~~~

Itu yang ingin kita pelajari.

---

## Daily batch vs one-hour forecast

Kita process daily files untuk workshop convenience.

Tapi prediction unit tetap hourly.

Jadi orchestration granularity dan model prediction granularity tidak harus identical.

Daily pipeline bisa prepare data, sementara model predict individual zone-hour target.

---

## Idempotent replay

Kalau Jan 27 direlease ulang, output sebaiknya deterministic.

Kenapa?

Karena retry itu normal.

Historical replay juga jadi latihan buat production pipeline habit:

> Same logical input should not randomly duplicate/corrupt output.

---

## Checkpoint

1. Kenapa historical data perlu direplay?
2. Apa bedanya replay source dan released raw batch?
3. Kenapa Jan 1–26 disiapkan dulu?
4. Bagaimana kita mencegah prediction melihat future?
5. Apa yang simulated dan apa yang tetap realistic?
