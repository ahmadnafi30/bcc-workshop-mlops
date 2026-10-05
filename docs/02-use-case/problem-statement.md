# Problem Statement — Kita Sebenarnya Lagi Predict Apa?

Sebelum ngomong MLOps, kita harus jelas dulu ML problem-nya.

Karena MLOps yang bagus nggak bisa menyelamatkan problem formulation yang kabur.

Use case kita:

> **Predict jumlah Yellow Taxi pickups di setiap Manhattan taxi zone untuk satu jam ke depan.**

Simple kalimatnya, tapi ada beberapa detail penting.

---

## Unit prediction kita

Model tidak predict “NYC demand” secara global.

Model predict per:

~~~text
zone
×
target hour
~~~

Contoh:

~~~text
Zone 161
Target hour: 2025-01-28 18:00
Prediction: 147 pickups
~~~

Jadi setiap row model merepresentasikan satu combination:

~~~text
one zone × one hour
~~~

---

## Kenapa satu jam ahead?

Kenapa nggak next 5 minutes? Kenapa nggak besok?

Karena satu jam cukup reasonable buat workshop:

- historical lag masih relevant,
- pattern harian masih strong,
- use case mudah dipahami,
- ground truth datang relatif cepat,
- monitoring/replay enak didemokan.

Satu jam juga bikin konsep online feature cukup jelas.

Untuk target 18:00, history terbaru yang boleh dipakai adalah sampai 17:00.

---

## Raw data granularity vs model granularity

NYC TLC raw data:

~~~text
one row
=
one taxi trip
~~~

Contoh:

| pickup time | zone |
| --- | ---: |
| 17:03 | 161 |
| 17:10 | 161 |
| 17:44 | 162 |

Model kita nggak butuh detail individual trip.

Kita aggregate:

| timestamp | zone_id | trip_count |
| --- | ---: | ---: |
| 17:00 | 161 | 2 |
| 17:00 | 162 | 1 |

Jadi transform utama pertama:

~~~text
trip events
↓
hourly demand time series
~~~

Ini penting karena model kita sebenarnya learning temporal demand pattern, bukan characteristic individual passenger.

---

## Input apa yang boleh dipakai?

Target:

~~~text
18:00
~~~

Boleh:

~~~text
17:00 demand
16:00 demand
yesterday 18:00
last week 18:00
recent rolling average
hour=18
day_of_week
~~~

Tidak boleh:

~~~text
actual 18:00 demand
future 19:00 demand
rolling window yang include 18:00 actual
~~~

Kenapa?

Karena waktu prediction dibuat, actual 18:00 belum diketahui.

Kalau model train pakai informasi future, validation metric bisa terlihat keren tapi production prediction impossible.

Itulah leakage.

---

## Business interpretation

Kalau model predict high demand di suatu zone, secara conceptual itu bisa bantu:

- fleet positioning,
- dispatch planning,
- capacity planning,
- demand awareness.

Workshop ini bukan claim bahwa model kita siap dipakai NYC operations.

Kita pakai scenario yang realistic enough buat lifecycle learning.

---

## Primary metric: MAE

MAE = Mean Absolute Error.

Formula intuition:

~~~text
absolute prediction errors
↓
average
~~~

Contoh:

~~~text
prediction = 150
actual = 160
error = 10

prediction = 80
actual = 70
error = 10
~~~

MAE ignore direction, focus magnitude.

Kalau:

~~~text
MAE = 10
~~~

intuition-nya:

> On average, prediction meleset sekitar 10 pickups per zone-hour.

Itu gampang dijelaskan ke non-ML audience.

---

## Secondary metric: RMSE

RMSE lebih sensitif ke large error.

Misalnya dua model punya MAE mirip, tapi salah satunya kadang miss ekstrem.

RMSE bisa lebih tinggi.

Makanya kita log both:

~~~text
MAE
→ easy average error interpretation

RMSE
→ more sensitive to big misses
~~~

---

## Kenapa baseline penting?

Baseline kita:

~~~text
prediction(t)
=
demand(t - 24h)
~~~

Alias:

> “Prediksi jam ini = demand jam yang sama kemarin.”

Kelihatannya sederhana.

Tapi taxi demand punya daily pattern, jadi baseline ini bisa cukup kuat.

Ini bagus.

Karena main model harus **earn its complexity**.

Kalau complex model kalah dari baseline simple, pertanyaan yang sehat adalah:

> “Kenapa kita pakai model lebih kompleks?”

bukan:

> “Gimana caranya tetap deploy model kompleks ini?”

---

## Success criteria model

Main model considered useful kalau:

~~~text
model MAE
<
baseline MAE
~~~

Tapi di MLOps context, success nggak berhenti di offline metric.

System juga harus:

- reproducible,
- servable,
- observable,
- maintainable.

Jadi ML metric adalah satu dimension dari project quality.

---

## Scope limitation

Kita fokus:

~~~text
Yellow Taxi
Manhattan
early 2025
one-hour horizon
pickup count
~~~

Kenapa Manhattan saja?

Supaya dataset lebih manageable tapi tetap punya banyak zones dan meaningful spatial variation.

Workshop goal bukan maximize NYC coverage.

Goal-nya punya use case cukup realistic tanpa bikin participant laptop menangis. 😭

---

## Checkpoint

Coba jawab:

1. Model kita predict apa exactly?
2. Satu row model represent apa?
3. Kenapa actual target hour nggak boleh jadi feature?
4. MAE 10 artinya apa secara intuitif?
5. Kenapa baseline lag_24h bukan baseline asal-asalan?
