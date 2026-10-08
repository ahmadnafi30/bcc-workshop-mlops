# Historical Replay — Gimana Kita Simulasikan Production Time Pakai Data Masa Lalu?

Ini salah satu concept yang kelihatannya simple, tapi sebenarnya penting banget buat seluruh workshop.

Dataset TLC kita historical. Artinya secara fisik kita bisa saja sudah punya January, February, dan March semuanya di laptop.

Kalau begitu kenapa nggak langsung load semua data, train, predict, evaluate, selesai?

Karena kalau kita mau belajar production-like lifecycle, **availability over time matters**.

Model di dunia nyata tidak punya akses ke future ground truth. Kalau workshop langsung membuka semua future data sekaligus, kita kehilangan temporal causality yang justru ingin kita pelajari.

Historical replay dibuat buat solve problem itu.

---

## Analogi paling gampang: pertandingan rekaman

Bayangin kalian punya full recording pertandingan sepak bola.

Video-nya lengkap sampai peluit akhir. Skor akhir technically sudah ada di file.

Tapi kalian mau latihan jadi live commentator.

Apakah kalian boleh scrub langsung ke menit 90 sebelum komentar menit 20?

Ya nggak.

Kalian harus play:

~~~text
minute 1
minute 2
minute 3
...
~~~

Future content physically ada, tapi secara logical kalian belum boleh melihatnya.

Historical replay bekerja seperti itu.

~~~text
full historical source
→ already exists

pipeline visibility
→ revealed gradually
~~~

Yang disimulasikan adalah **waktu availability**, bukan isi datanya.

---

## Source yang lengkap vs data yang sudah released

Bootstrap menyiapkan compact monthly replay source:

~~~text
data/source/replay/
~~~

Anggap ini seperti full recording.

Pipeline production simulation tidak langsung consume semua rows.

Untuk logical date Jan 27, kita release hanya Jan 27:

~~~text
monthly replay source
↓
filter target date
↓
data/raw/trips/2025-01-27.csv
~~~

Sekarang downstream pipeline behave seolah:

> “Batch Jan 27 baru datang.”

Padahal secara physical semua source month sudah ada.

---

## Kenapa ada banyak layer folder?

Kadang beginner lihat:

~~~text
data/source
data/raw
data/processed
data/features
data/snapshots
~~~

dan merasa:

> “Kenapa file-nya nggak satu folder aja?”

Karena setiap layer punya semantics beda.

### source

External/historical source yang kita prepare.

### raw

Data yang sudah logically released ke production pipeline.

### processed

Trip-level events sudah ditransform jadi hourly demand.

### features

Combined history yang sudah punya lag/calendar/rolling features.

### snapshots

Frozen training input untuk specific training cycle.

Jadi folder structure sebenarnya merepresentasikan data lifecycle.

---

## Simulate satu hari

Command:

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Output:

~~~text
data/raw/trips/2025-01-27.csv
~~~

Apa yang terjadi di belakang?

~~~text
parse target date
↓
resolve month = 2025-01
↓
open January replay source
↓
select rows on Jan 27
↓
write one daily raw batch
~~~

Satu logical day sekarang tersedia buat downstream.

---

## Kenapa raw daily batch masih trip-level?

Karena raw layer merepresentasikan event yang datang.

Satu row:

~~~text
one taxi trip
~~~

Model target kita:

~~~text
pickup count
per zone
per hour
~~~

Jadi raw data masih harus diaggregate.

~~~text
raw event
→ aggregation
→ model-oriented signal
~~~

---

## Aggregate ke hourly demand

Daily batch diproses:

~~~text
many taxi trip rows
↓
group by pickup hour + zone
↓
complete all zone-hour combinations
↓
fill zero pickup combinations
↓
processed hourly demand
~~~

Output:

~~~text
data/processed/demand/2025-01-27.csv
~~~

Sekarang satu row berarti:

~~~text
one zone
×
one hour
~~~

---

## Kenapa zero-demand combination harus ada?

Suppose zone 161 jam 03:00 tidak punya satu pun trip.

Kalau kita hanya group rows yang exist, row itu hilang.

Apakah artinya data missing?

Belum tentu.

Dalam domain kita:

> “Demand = 0.”

Kalau row hilang total, time-series bisa mengira jam itu missing dan lag/rolling sequence jadi tidak continuous.

Makanya pipeline create complete grid.

Ini detail kecil dengan impact besar ke model.

---

## Initial history — kenapa Jan 1 sampai Jan 26 sudah disiapkan?

Sebelum simulation production dimulai, kita butuh initial model.

Lag terpanjang:

~~~text
168 hours
=
7 days
~~~

Jadi:

~~~text
Jan 1–7
→ warm-up history
~~~

Kemudian:

~~~text
Jan 8–21
→ training

Jan 22–26
→ validation
~~~

Setelah initial champion established:

~~~text
Jan 27 onward
→ production-like replay
~~~

Ini mirip real deployment. Sebelum model diluncurkan, kita memang sudah punya historical training data.

---

## Kenapa initial history tidak direplay satu-satu?

Secara technical bisa trigger Jan 1 sampai Jan 26 satu per satu.

Tapi workshop akan habis hanya buat click runs.

Makanya ada bootstrap historical preparation.

~~~text
initial historical context
→ prepared efficiently

production-like period
→ replay gradually
~~~

Concept temporal tetap terjaga di area yang ingin kita demo.

---

## Prediction timing — bagian paling penting

Suppose target:

~~~text
Jan 28 18:00
~~~

One-hour-ahead prediction secara logical dibuat sebelum target demand complete.

Feature provider hanya boleh lihat history sebelum target.

Misalnya:

~~~text
lag_1h
→ 17:00

lag_24h
→ yesterday 18:00
~~~

Actual demand Jan 28 18:00 adalah target.

Tidak boleh jadi input.

---

## “Tapi file Jan 28 full sudah ada di disk?”

Good question.

Historical simulation memang punya physical future data somewhere.

Yang menjaga realism adalah **application logic dan release boundaries**.

Kalau serving feature provider blindly read future timestamp, kita punya leakage.

Replay sendiri tidak magically prevent semua leakage.

Kita tetap enforce:

~~~text
feature timestamps
<
target timestamp
~~~

Jadi temporal correctness punya beberapa layer:

1. daily release boundary;
2. preprocessing boundary;
3. online feature query boundary.

---

## Delayed ground truth

Setelah target hour selesai, actual baru bisa dinilai.

~~~text
before 18:00
→ prediction exists

18:00–18:59
→ actual trips happen

afterward
→ ground truth complete
→ prediction can be evaluated
~~~

Ini yang bikin monitoring ML berbeda dari normal HTTP monitoring.

HTTP latency known immediately.

Prediction correctness delayed.

---

## Replay mempercepat clock, bukan menghapus causality

Workshop bisa melakukan Jan 27, Jan 28, Jan 29 dalam satu session.

Real world butuh tiga hari.

Apa yang fake?

Tapi prediction unit tetap hourly.

Apa yang tetap real secara dependency?

~~~text
data release
↓
prediction
↓
ground truth later
↓
evaluation
↓
retraining decision
~~~

Ini alasan replay powerful buat teaching MLOps.

---

## Daily orchestration vs hourly prediction

Ada nuance:

> “Kalau model predict one hour ahead, kenapa data pipeline per day?”

Karena orchestration granularity dan inference granularity tidak harus sama.

Daily batch bisa prepare:

~~~text
24 hours × all zones
~~~

Serving masih bisa request:

~~~text
one target hour
×
one zone
~~~

Production architecture juga sering punya batch feature preparation tapi online request granularity berbeda.

Yang penting availability rules konsisten.

---

## Idempotency

Suppose Jan 27 release task fail halfway lalu di-retry.

Kalau retry menghasilkan duplicate rows:

~~~text
first attempt
→ 100k rows

retry append
→ same 100k rows again
~~~

features dan monitoring rusak.

Kita ingin:

~~~text
same logical date
↓
same deterministic output
~~~

Idempotency membuat retries lebih aman.

---

## Logical time vs wall-clock time

Airflow run hari ini secara real-world mungkin tanggal 2026.

Tapi replay_date:

~~~text
2025-01-27
~~~

adalah logical data time.

Jangan campur:

~~~text
when workshop run happened
vs
which production date is being simulated
~~~

Dalam data engineering, logical time sering lebih important daripada machine clock.

---

## Potential production differences

Real production mungkin punya:

~~~text
stream/event source
object storage partition
data warehouse
hourly ingestion
timezone-aware timestamp
late-arriving data
backfill
~~~

Workshop menyederhanakan itu.

Tapi replay already teaches:

- partitioned time;
- delayed availability;
- backfill-like execution;
- idempotent rerun;
- causal feature access.

Concept-nya transferable.

---

## Thought experiment: apa yang terjadi kalau kita cheat?

Misalnya target Jan 28 18:00.

Feature builder accidentally pakai actual demand 18:00.

Offline MAE bisa turun fantastis.

Apakah MLOps pipeline menjadi bagus?

No.

Kita cuma otomatis mengelola cheating model dengan sangat profesional. 😭

Reminder:

> Correct ML semantics always come before fancy tooling.

---

## Checkpoint

Coba jawab dengan bahasa sendiri:

1. Kenapa historical data perlu direplay?
2. Apa yang sebenarnya disimulasikan oleh replay?
3. source/replay/raw/processed beda semantics apa?
4. Kenapa Jan 1–26 disiapkan sebelum production simulation?
5. Kenapa zero-demand row harus explicit?
6. Prediction Jan 28 18:00 boleh lihat data jam berapa saja?
7. Kenapa future data physically ada tapi tetap nggak boleh dipakai?
8. Ground truth delayed artinya apa?
9. Daily batch orchestration boleh coexist dengan hourly prediction kenapa?
10. Idempotency penting buat retry bagaimana?
11. Logical date beda apa dengan real workshop clock?
12. Kalau replay bagus tapi feature provider leak future, apakah simulation masih valid?

Kalau semua kebayang, historical replay bukan lagi “script fake tanggal”, tapi benar-benar tool untuk preserve temporal causality saat workshop.
