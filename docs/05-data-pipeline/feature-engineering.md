# Feature Engineering — Dari Hourly Demand Jadi Input yang Bisa Dipelajari Model

Sekarang kita sudah punya processed demand yang bentuknya jauh lebih clean dibanding raw taxi trips.

Satu row kurang lebih berarti:

~~~text
timestamp
zone_id
trip_count
~~~

Contoh:

~~~text
2025-01-10 17:00
zone 161
142 pickups
~~~

Pertanyaannya:

> “Apakah model tinggal dikasih tiga column itu?”

Belum.

Karena model kita perlu context temporal. Angka 142 sendiri kurang meaningful kalau kita nggak tahu:

- jam berapa;
- hari apa;
- satu jam sebelumnya demand berapa;
- kemarin jam yang sama berapa;
- minggu lalu jam yang sama berapa;
- recent trend naik atau turun.

Feature engineering mengubah historical demand menjadi **informasi yang bisa dipakai model untuk belajar pattern**.

---

## Goal akhir

Command:

~~~bash
uv run python scripts/build_features.py
~~~

Output:

~~~text
data/features/taxi_demand_features.csv
~~~

Row model-ready punya feature seperti:

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
target_trip_count
~~~

Jangan lihat list ini sebagai column random.

Masing-masing punya intuition.

---

## Feature engineering bukan “buat column sebanyak mungkin”

Ada misconception:

> “Semakin banyak feature berarti model makin bagus.”

Nggak selalu.

Feature harus punya alasan.

Kalau feature:

- leakage;
- noisy;
- unavailable saat serving;
- redundant banget;
- semantics-nya berubah antara train dan inference;

dia justru bisa bikin system lebih jelek.

Workshop ini sengaja pakai feature yang mudah dijelaskan dan bisa tersedia saat prediction time.

---

## Step 1 — Sorting: kenapa urutan row matters?

Time-series operation sangat bergantung sequence.

Suppose satu zone punya rows:

~~~text
18:00
16:00
17:00
~~~

Kalau kita langsung shift:

~~~text
previous row
~~~

belum tentu previous **time**.

Makanya kita sort:

~~~text
zone_id
timestamp
~~~

Menjadi:

~~~text
zone 161
16:00
17:00
18:00

zone 162
16:00
17:00
18:00
~~~

Baru operation temporal meaningful.

Rule:

> Row order bukan cosmetic detail kalau kita pakai shift/rolling.

---

## Step 2 — Calendar features

Dari timestamp kita derive:

~~~text
hour
day_of_week
is_weekend
~~~

Kenapa timestamp mentah tidak cukup?

Model tabular tidak otomatis memahami bahwa:

~~~text
18:00
~~~

sering punya behavior berbeda dengan:

~~~text
03:00
~~~

atau:

~~~text
Monday
~~~

beda dengan Saturday.

Calendar feature expose structure.

---

## Apakah calendar feature leakage?

Target time sendiri known sebelum prediction.

Kalau kita mau predict:

~~~text
2025-01-28 18:00
~~~

kita sudah tahu:

- hour = 18;
- day of week;
- weekend atau bukan.

Jadi safe.

Contrast dengan:

~~~text
actual_trip_count_18_00
~~~

yang belum known.

Feature availability adalah question utama:

> “Apakah value ini sudah diketahui ketika prediction dibuat?”

---

## Step 3 — Lag features

Lag berarti historical value beberapa step ke belakang.

Kita punya:

~~~text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
~~~

Untuk target:

~~~text
Jan 28 18:00
~~~

maka:

~~~text
lag_1h
→ Jan 28 17:00

lag_2h
→ Jan 28 16:00

lag_24h
→ Jan 27 18:00

lag_168h
→ Jan 21 18:00
~~~

Per-zone grouping critical.

Kalau tidak, boundary antar zone contamination.

---

## Kenapa lag ini masuk akal buat taxi demand?

Demand punya temporal pattern.

### Recent momentum

Kalau 17:00 sangat ramai, 18:00 mungkin masih ramai.

~~~text
lag_1h
lag_2h
lag_3h
~~~

capture recent context.

### Daily seasonality

Jam 18:00 hari ini mungkin mirip jam 18:00 kemarin.

~~~text
lag_24h
~~~

### Weekly seasonality

Tuesday 18:00 mungkin lebih mirip Tuesday minggu lalu daripada Monday kemarin.

~~~text
lag_168h
~~~

Feature design harus connect ke domain intuition.

---

## Kenapa lag harus per zone?

Ini critical.

Suppose dataframe sorted globally:

~~~text
zone 161 18:00
zone 162 18:00
zone 163 18:00
~~~

Kalau shift tanpa group by zone, “previous row” bisa berasal dari zone lain.

Contoh bug:

~~~text
target:
zone 162 18:00

lag_1h accidentally:
zone 161 18:00
~~~

Secara code mungkin tidak error.

Secara semantics fatal.

Makanya lag dibuat:

~~~text
group by zone_id
↓
shift within each zone
~~~

Ini contoh bug yang test harus catch.

---

## Step 4 — Rolling features

Lag memberi exact historical point.

Rolling memberi summary recent history.

Kita shift history dulu.

Then rolling.

~~~text
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Untuk target 18:00, rolling 3h seharusnya memakai:

~~~text
15:00
16:00
17:00
~~~

bukan include 18:00.

---

## Kenapa shift sebelum rolling?

Kalau kita langsung:

~~~text
rolling(window=3)
~~~

pada row target 18:00, default rolling bisa include current row.

Sekarang target demand masuk feature.

Leakage.

Makanya pattern:

~~~text
trip_count
↓
shift(1)
↓
rolling(...)
~~~

Jadi current target dikeluarkan lebih dulu.

Ini satu line implementation yang punya impact besar ke validity model.

---

## Analogi leakage

Bayangin ujian.

Kalian mau predict nilai siswa berdasarkan:

- jam belajar;
- attendance;
- nilai sebelumnya.

Valid.

Tapi salah satu feature ternyata:

~~~text
final_exam_score
~~~

Itu bukan prediksi lagi.

Kalian kasih jawaban ke model.

Time-series leakage sering lebih subtle karena current/future values bisa masuk rolling window tanpa sadar.

---

## Step 5 — Target

Target kita:

~~~text
target_trip_count
=
trip_count current hour
~~~

Jadi satu row punya structure:

~~~text
features from past/context
↓
predict
↓
current hour trip_count
~~~

Misalnya:

~~~text
hour = 18
lag_1h = 142
lag_24h = 155
rolling_mean_3h = 139.7
target_trip_count = 165
~~~

Model belajar mapping history → current target.

---

## Step 6 — Warm-up period

Feature terpanjang:

~~~text
lag_168h
~~~

Butuh 168 hours history.

Row Jan 1 tidak punya one-week-before data.

Row Jan 4 juga belum.

Makanya Jan 1–7 berfungsi sebagai:

~~~text
history buffer
~~~

Feature-complete rows mulai sekitar Jan 8.

Important:

> Warm-up rows bukan data sia-sia.

Walaupun tidak dipakai sebagai training target, mereka menyediakan historical context buat rows berikutnya.

---

## Kenapa incomplete rows di-drop?

Model input contract mengharapkan semua required lag/rolling features tersedia.

Option lain bisa pakai imputation.

Tapi untuk workshop, dropping warm-up rows lebih transparent karena missing-nya structural:

> memang belum ada history satu minggu.

Mengisi lag_168h dengan zero bisa memberi meaning palsu:

~~~text
zero demand
~~~

padahal sebenarnya:

~~~text
unknown because history unavailable
~~~

Missing dan zero beda semantics.

---

## Batch feature engineering vs online feature engineering

Training:

~~~text
many historical rows
↓
build features in bulk
~~~

Serving:

~~~text
one request
zone + target time
↓
lookup history
↓
build one model row
~~~

Implementation-nya beda.

Semantics-nya harus sama.

Ini disebut:

> **training-serving consistency**

Kalau batch lag_24h berarti yesterday same hour, online lag_24h juga harus persis itu.

---

## Kenapa nggak reuse satu function exactly untuk batch dan online?

Kadang bisa.

Tapi workload shape berbeda.

Batch:

- vectorized;
- many zones;
- many timestamps.

Online:

- one target;
- targeted history lookup;
- latency-sensitive.

Yang lebih penting daripada function identity adalah **feature contract identity**.

Same meaning, same types, same ordering.

---

### Batch vs online feature path

Model expected columns disimpan sebagai constant.

Kenapa?

Suppose training order:

~~~text
hour
day_of_week
lag_1h
lag_24h
~~~

Serving accidentally:

~~~text
hour
lag_1h
day_of_week
lag_24h
~~~

Beberapa model/pipeline bisa salah interpret.

Explicit feature list membuat input deterministic.

---

## zone_id sebagai categorical

Zone ID itu identifier.

~~~text
zone 200
~~~

bukan berarti mathematically dua kali zone 100.

Kalau diperlakukan continuous numeric, model bisa infer ordinal relation yang tidak meaningful.

Makanya zone_id diperlakukan categorical.

Ini juga harus konsisten saat serving.

---

## Testing feature engineering — kenapa synthetic data powerful?

Real TLC data kompleks.

Kalau test fail:

~~~text
expected 137.42
got 138.11
~~~

kita susah manual reason.

Synthetic sequence:

~~~text
0, 1, 2, ..., 199
~~~

jauh lebih gampang.

Untuk hour index 168:

~~~text
lag_1h = 167
lag_24h = 144
lag_168h = 0
~~~

Expected values bisa dihitung kepala.

Test jadi interpretable.

---

## Leakage test rolling mean

Synthetic sequence sama.

Target 168.

Rolling 3h harus dari:

~~~text
165
166
167
~~~

Mean:

~~~text
166
~~~

Kalau result include 168, mean berubah.

Test langsung expose leakage.

---

## Cross-zone contamination test

Buat dua zones dengan scale beda.

~~~text
zone A:
0,1,2,...

zone B:
1000,1001,1002,...
~~~

Kalau lag zone B tiba-tiba 199 dari zone A, grouping bug ketahuan.

Ini example bagus bagaimana test design berasal dari failure mode.

---

## Feature engineering dan retraining

Saat new daily demand masuk:

~~~text
history grows
↓
feature dataset rebuilt
~~~

Later retraining snapshot diambil dari feature dataset terbaru sampai cutoff.

Artinya bug feature engineering tidak hanya impact one model run.

Dia bisa propagate ke:

- DVC snapshot;
- MLflow experiments;
- serving expectations;
- monitoring;
- retraining.

Makanya feature code adalah core business logic, bukan utility kecil.

---

## Feature availability checklist

Sebelum tambah feature baru, tanya:

### Apakah tersedia saat prediction?

Kalau no, leakage risk.

### Apakah semantics konsisten offline/online?

Kalau no, training-serving skew.

### Apakah data source reliable?

Kalau weather API sering missing, serving strategy perlu fallback.

### Apakah feature benar-benar punya intuition?

Kalau tidak, jangan tambah cuma karena mudah.

---

## Optional weather features

Future extension:

~~~text
temperature
rain
snow
wind
~~~

Potential benefit: taxi demand bisa dipengaruhi weather.

Tapi menambah external source berarti menambah MLOps responsibility:

~~~text
weather ingestion
↓
availability
↓
schema validation
↓
join timing
↓
serving availability
↓
monitoring
~~~

Feature baru bukan cuma modeling decision.

Dia juga systems decision.

Ini alasan weather tetap optional.

---

## Common failure modes

### Lag salah karena sort salah

Symptom: weird lag values.

### Cross-zone contamination

Symptom: historical value berasal dari zone lain.

### Rolling include target

Symptom: suspiciously great validation performance.

### Missing history dianggap zero

Symptom: artificial pattern di warm-up rows.

### Batch vs online mismatch

Symptom: offline MAE bagus, serving prediction aneh.

### Categorical dtype berubah

Symptom: model inference error atau semantics berubah.

---

## Mini exercise

Target:

~~~text
zone 161
Jan 28 18:00
~~~

Available history:

~~~text
15:00 = 120
16:00 = 130
17:00 = 140
yesterday 18:00 = 150
last week 18:00 = 145
~~~

Coba isi:

~~~text
lag_1h = ?
lag_2h = ?
lag_3h = ?
lag_24h = ?
lag_168h = ?
rolling_mean_3h = ?
~~~

Expected:

~~~text
lag_1h = 140
lag_2h = 130
lag_3h = 120
lag_24h = 150
lag_168h = 145
rolling_mean_3h = 130
~~~

Kalau kalian bisa derive manual, feature semantics-nya clear.

---

### Feature schema contract

1. Kenapa sort harus sebelum lag?
2. Calendar feature aman dari leakage kenapa?
3. Lag 24h dan 168h capture pattern apa?
4. Kenapa group by zone mandatory?
5. Kenapa rolling harus shift dulu?
6. Missing history beda apa dengan zero demand?
7. Warm-up rows masih useful walaupun nggak jadi target training kenapa?
8. Batch dan online feature path boleh beda implementation kenapa?
9. Apa yang harus sama antara training dan serving?
10. zone_id kenapa categorical?
11. Synthetic sequence bagus buat test kenapa?
12. Feature baru seperti weather menambah system responsibility apa saja?
13. Offline metric terlalu bagus bisa jadi tanda leakage bagaimana?

Kalau semua kebayang, kalian sudah ngerti feature engineering bukan sekadar “nambah column”, tapi salah satu contract paling penting di seluruh ML system.
