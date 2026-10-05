# Problem Statement — What Are We Predicting?

## Use case kita simple, tapi cukup realistic

Kita mau memprediksi:

> **berapa banyak Yellow Taxi pickup yang akan terjadi di setiap Manhattan taxi zone satu jam ke depan.**

Misalnya sekarang kita sedang punya historical information sampai:

~~~text
2025-01-28 17:00
~~~

Kita ingin predict:

~~~text
Zone 161
2025-01-28 18:00
~~~

Output kira-kira:

~~~text
predicted_trip_count = 147.8
~~~

Karena model regression, output bisa float. Secara business kalau nanti perlu count bulat bisa ada post-processing, tapi core model tetap regression.

---

# Kenapa one hour ahead?

Kita sengaja pilih horizon satu jam karena cukup gampang dijelaskan dan cukup meaningful.

Kalau terlalu pendek, misalnya satu menit, data pipeline dan behavior demand berbeda.

Kalau terlalu jauh, misalnya satu minggu, historical short-term pattern jadi kurang powerful dan problem forecasting-nya lebih kompleks.

Satu jam memberi kita balance:

~~~text
recent demand
still useful

daily pattern
still useful

weekly pattern
still useful
~~~

---

# Raw data-nya seperti apa?

NYC Yellow Taxi Trip Records punya satu row per trip.

Secara simplified:

| pickup datetime | PULocationID |
| --- | ---: |
| 2025-01-10 17:03 | 161 |
| 2025-01-10 17:10 | 161 |
| 2025-01-10 17:44 | 162 |

Model kita nggak langsung predict individual trip.

Kita aggregate.

Hasilnya:

| timestamp | zone_id | trip_count |
| --- | ---: | ---: |
| 2025-01-10 17:00 | 161 | 2 |
| 2025-01-10 17:00 | 162 | 1 |

Jadi setelah preprocessing:

~~~text
1 row
=
1 zone × 1 hour
~~~

---

# Target variable

Target kita:

~~~text
target_trip_count
~~~

Untuk row:

~~~text
zone 161
18:00
~~~

target adalah jumlah actual pickup yang terjadi antara:

~~~text
18:00
sampai sebelum
19:00
~~~

---

# Model boleh lihat apa?

Ini bagian penting karena langsung berhubungan ke leakage.

Untuk predict 18:00, model boleh melihat:

~~~text
17:00 demand
16:00 demand
15:00 demand
yesterday 18:00
last week 18:00
hour of day
day of week
weekend flag
~~~

Model tidak boleh lihat:

~~~text
actual 18:00 demand
future 19:00 demand
rolling average yang include 18:00 actual
~~~

Karena itu information yang belum tersedia saat prediction dibuat.

---

# Contoh leakage secara gampang

Misalnya kalian mau predict nilai ujian besok.

Feature kalian:

~~~text
jam belajar hari ini
jumlah latihan
attendance
~~~

masih fair.

Tapi kalau feature-nya:

~~~text
nilai ujian besok
~~~

ya jelas model terlihat hebat.

Tapi bukan karena pintar.

Karena jawabannya bocor.

Time-series leakage sering lebih subtle.

Misalnya:

~~~text
rolling_mean_3h
~~~

Kelihatannya valid.

Tapi kalau rolling calculation include current target hour, sebenarnya ada sebagian answer di input.

Makanya implementation detail seperti shift(1) sebelum rolling itu penting.

---

# Scope workshop

Biar project tetap manageable, kita scope ke:

~~~text
Taxi type:
Yellow Taxi

Area:
Manhattan

Prediction:
Pickup count

Horizon:
1 hour ahead

Main historical period:
early 2025
~~~

Kenapa Manhattan?

Karena:

- zone cukup banyak,
- demand tinggi,
- dataset masih meaningful,
- workshop tetap reasonable secara resource.

---

# Metric utama: MAE

Kita pakai:

~~~text
MAE
Mean Absolute Error
~~~

Formula konsepnya:

~~~text
average(
  absolute(prediction - actual)
)
~~~

Misalnya:

~~~text
actual     prediction    error
100        110           10
150        140           10
80         95            15
~~~

MAE memberi average absolute error.

Kalau:

~~~text
MAE = 10
~~~

interpretasinya cukup natural:

> Model rata-rata meleset sekitar 10 pickups per zone-hour.

Itu enak buat explain ke non-ML people.

---

# Metric kedua: RMSE

Kita juga simpan:

~~~text
RMSE
Root Mean Squared Error
~~~

Kenapa perlu?

RMSE memberi penalty lebih besar ke big errors.

Jadi dua model bisa punya MAE mirip tapi salah satu punya beberapa catastrophic miss yang bikin RMSE lebih tinggi.

Kita tidak menjadikan RMSE primary metric, tapi tetap useful sebagai secondary view.

---

# Baseline: yesterday same hour

Sebelum training ML model, kita punya simple rule:

~~~text
prediction(t)
=
demand(t - 24h)
~~~

Artinya:

> Prediksi demand jam 18:00 hari ini pakai demand jam 18:00 kemarin.

Kenapa baseline seperti ini masuk akal?

Taxi demand punya daily seasonality.

Morning rush hari ini sering punya relation dengan morning rush hari sebelumnya.

Baseline ini cukup simple, tapi nggak deliberately stupid.

Itu penting.

Karena model ML harus earn complexity-nya.

---

# Kenapa model harus beat baseline?

Coba bayangin:

~~~text
Naive baseline MAE = 10

Fancy ML model MAE = 13
~~~

Apakah fancy model worth it?

Probably not.

Kita menambah:

- training,
- model artifact,
- serving,
- monitoring,
- maintenance.

Tapi hasil lebih buruk.

Jadi kita punya gate:

> Kalau model utama tidak beat baseline, jangan langsung register sebagai challenger.

Ini mengajarkan satu habit bagus:

~~~text
Complexity must justify itself.
~~~

---

# Kenapa use case ini enak buat MLOps?

Karena lifecycle-nya natural.

Prediction sekarang:

~~~text
17:00
predict 18:00
~~~

Ground truth belum ada.

Setelah 18:00 lewat:

~~~text
actual demand becomes known
~~~

Sekarang kita bisa calculate error.

Kalau performa makin jelek:

~~~text
monitoring
↓
retraining
↓
new challenger
~~~

Jadi seluruh MLOps loop bisa kita demonstrate tanpa memaksakan cerita.
