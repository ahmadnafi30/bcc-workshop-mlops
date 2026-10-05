# Feature Engineering — How Do We Turn History Into Predictive Signals?

## Model nggak bisa makan “timestamp” mentah lalu magically ngerti semuanya

Setelah aggregation, data kita bentuknya kira-kira:

| timestamp | zone_id | trip_count |
| --- | ---: | ---: |
| 2025-01-10 17:00 | 161 | 142 |
| 2025-01-10 18:00 | 161 | 165 |

Target kita untuk row 18:00:

~~~text
target_trip_count = 165
~~~

Sekarang pertanyaannya:

> “Informasi apa yang tersedia sebelum 18:00 dan likely useful buat predict 18:00?”

Itulah feature engineering.

---

# Calendar Features

Kita extract:

~~~text
hour
day_of_week
is_weekend
~~~

Kenapa?

Karena behavior demand sangat time-dependent.

Coba bayangin:

~~~text
Monday 08:00
vs
Sunday 03:00
~~~

Walaupun zone sama, expectation demand bisa sangat beda.

Raw timestamp sendiri punya banyak component.

Kita encode pattern yang lebih directly useful.

---

# zone_id

Kita pakai:

~~~text
zone_id
~~~

Tapi treat as categorical.

Kenapa?

Karena:

~~~text
zone 200
~~~

nggak berarti “dua kali zone 100”.

Angka itu identifier, bukan meaningful magnitude.

Kalau dianggap numeric ordinal biasa, model bisa infer relation yang nggak kita maksud.

---

# Lag Features

Lag adalah previous value.

Features:

~~~text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
~~~

Untuk target:

~~~text
2025-01-10 18:00
~~~

maka:

~~~text
lag_1h
= Jan 10 17:00

lag_2h
= Jan 10 16:00

lag_24h
= Jan 9 18:00

lag_168h
= Jan 3 18:00
~~~

---

# Kenapa lag 1, 24, 168?

Mereka represent beberapa temporal pattern.

## lag_1h

Recent momentum.

Kalau area lagi ramai satu jam sebelumnya, next hour mungkin masih ramai.

## lag_24h

Daily seasonality.

Jam 18 hari ini sering related dengan jam 18 kemarin.

## lag_168h

Weekly seasonality.

168 hours = 7 days.

Jadi Friday 18:00 bisa dibandingkan dengan Friday sebelumnya.

---

# Analogi gampang

Kalian ditanya:

> “Besok jam makan siang kantin bakal ramai nggak?”

Mungkin kalian mikir:

- sekarang lagi ramai nggak?
- kemarin jam segini ramai nggak?
- minggu lalu hari yang sama ramai nggak?

Lag features essentially formalize thought process itu.

---

# Rolling Features

Kita juga punya:

~~~text
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Rolling mean menjawab:

> “Secara average, beberapa jam terakhir demand-nya bagaimana?”

Contoh:

~~~text
15:00 = 100
16:00 = 120
17:00 = 140
~~~

rolling_mean_3h untuk target 18:00:

~~~text
(100 + 120 + 140) / 3
= 120
~~~

Ini memberi smoother signal daripada hanya satu previous hour.

---

# Ini bagian leakage yang paling penting

Kalau kita careless, rolling mean bisa accidentally include current target.

Misalnya target 18:00.

Bad logic:

~~~text
rolling window:
16:00
17:00
18:00 actual
~~~

Problem:

18:00 actual adalah answer.

Model jadi melihat target-nya sendiri.

Validation bisa terlihat sangat bagus tapi fake.

Correct logic:

~~~text
shift(1)
↓
rolling()
~~~

Jadi window berakhir di 17:00.

---

# Warm-up period

Feature terjauh:

~~~text
lag_168h
~~~

Artinya kita butuh minimum 168 hours history.

Kalau data mulai Jan 1:

~~~text
Jan 1
belum punya 7-day history

...

Jan 7
masih warm-up

Jan 8
first complete rows begin
~~~

Makanya:

~~~text
Jan 1–7
historical context

Jan 8 onward
model-ready rows
~~~

Ini bukan data terbuang.

Jan 1–7 dipakai sebagai context untuk lag.

---

# Per-zone grouping itu wajib

Coba bayangin table sorted wrong:

~~~text
zone 161
zone 162
zone 163
~~~

Kalau shift dilakukan tanpa groupby zone, lag zone 162 bisa accidentally mengambil previous row dari zone 161.

Itu nonsense.

Jadi pattern-nya:

~~~text
sort by:
zone_id
timestamp

then:
groupby(zone_id)

then:
shift / rolling
~~~

Time-series transformation harus respect entity boundary.

---

# Target

Kita copy:

~~~text
trip_count
→ target_trip_count
~~~

untuk current row.

Feature hanya historical.

Target current.

Ini membuat schema jelas.

---

# Main model

Kita pakai:

~~~text
HistGradientBoostingRegressor
~~~

Kenapa bukan LSTM?

Kenapa bukan Transformer?

Kenapa bukan Chronos?

Bukan karena model advanced jelek.

Tapi workshop goal utama adalah MLOps.

Kita butuh model yang:

- cukup strong,
- train cepat,
- CPU-friendly,
- dependency ringan,
- gampang diserve.

HistGradientBoosting cocok.

Kalau model terlalu berat, workshop berubah jadi:

> “nunggu training / download model.”

Bukan belajar lifecycle.

---

# Baseline

Model utama dibanding:

~~~text
prediction = lag_24h
~~~

Jadi naive baseline literally:

> “Demand jam yang sama kemarin berapa?”

Kenapa baseline ini bagus?

Karena secara domain masuk akal.

Kalau model ML tidak beat ini, berarti ML complexity belum justified.

---

# Train / validation split

Time-series harus hati-hati.

Kita tidak random split.

Kenapa?

Bayangin training melihat February tapi validation berisi January.

Secara chronological, model sudah melihat future relative ke validation.

Itu tidak represent realistic deployment.

Jadi:

~~~text
past
→ train

future
→ validation
~~~

Initial:

~~~text
Jan 8–21
training

Jan 22–26
validation
~~~

Retraining nanti:

~~~text
all older data
training

latest 5 days
validation
~~~

Validation window ikut maju.

---

# Training-serving consistency

Saat training, kita build:

~~~text
lag_1h
lag_24h
rolling_mean_3h
...
~~~

Saat API serving, kita juga harus build feature dengan definition yang sama.

Kalau training:

~~~text
rolling_mean_3h
=
mean of last 3 completed hours
~~~

tapi serving:

~~~text
rolling_mean_3h
=
mean of another window
~~~

model menerima semantics berbeda.

Itu disebut training-serving skew.

Dalam production system besar bisa dipakai feature store untuk manage consistency.

Di workshop kita implement explicit logic supaya concept-nya kelihatan.

---

# Feature checklist

Sebelum percaya dataset, selalu cek:

### Apakah row sorted?

~~~text
zone_id
timestamp
~~~

### Apakah lag dihitung per zone?

Harus iya.

### Apakah rolling exclude current target?

Harus iya.

### Apakah early incomplete row di-drop?

Iya.

### Apakah zone_id treated categorical?

Iya.

Kalau semua ini benar, barulah model metric lebih believable.
