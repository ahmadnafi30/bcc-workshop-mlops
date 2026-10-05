# Feature Engineering — Model Time Series Nggak Bisa Dikasih Timestamp Mentah Doang

Sekarang kita sudah punya hourly demand.

Contoh:

| timestamp | zone_id | trip_count |
| --- | ---: | ---: |
| 17:00 | 161 | 142 |
| 18:00 | 161 | 165 |

Target row 18:00:

~~~text
target_trip_count = 165
~~~

Model butuh features yang menggambarkan context sebelum 18:00.

---

## Calendar Features

Kita extract:

~~~text
hour
day_of_week
is_weekend
~~~

Kenapa?

Karena timestamp raw tidak otomatis memberi model semantic pattern.

Taxi demand jam 08:00 Monday mungkin beda dengan 23:00 Saturday.

Calendar feature expose pattern tersebut.

---

## Lag Features

Lag = previous value.

Kita pakai:

~~~text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
~~~

Untuk target 18:00:

~~~text
lag_1h
→ 17:00

lag_2h
→ 16:00

lag_24h
→ yesterday 18:00

lag_168h
→ same hour last week
~~~

Kenapa lag_168h?

Karena weekly seasonality bisa exist.

Monday 18:00 mungkin lebih similar dengan previous Monday 18:00 daripada Sunday 18:00.

---

## Analogi cafe

Kalau ditanya:

> “Besok jam 8 pagi cafe ramai nggak?”

Kalian mungkin lihat:

- sekarang seberapa ramai,
- kemarin jam 8,
- minggu lalu jam 8,
- average beberapa jam terakhir.

Lag feature formalize intuition itu.

---

## Rolling Features

Kita pakai:

~~~text
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Rolling mean capture local trend.

Kalau demand recent sedang naik, average recent bisa informative.

---

## Leakage trap di rolling feature

Ini super important.

Target 18:00.

Kalau rolling window include:

~~~text
16:00
17:00
18:00
~~~

berarti feature include actual target.

Cheating.

Correct flow:

~~~text
shift by 1 hour
↓
rolling
~~~

Jadi window end di 17:00.

Rule:

> Feature boleh melihat past, bukan target/future.

---

## Group by zone

Lag harus dihitung **per zone**.

Bad:

~~~text
sort all rows
shift globally
~~~

Bisa bikin previous row zone 161 jadi lag untuk zone 162.

Nonsense.

Correct:

~~~text
group by zone_id
↓
sort by timestamp
↓
shift / rolling
~~~

---

## Kenapa sorting penting?

Shift dan rolling assume order.

Kalau timestamp shuffled:

~~~text
18:00
14:00
17:00
~~~

shift jadi meaningless.

Jadi before time-series operation:

~~~text
sort zone
sort time
~~~

Simple, tapi critical.

---

## Warm-up Period

Longest lag:

~~~text
168 hours
=
7 days
~~~

Artinya row pertama belum punya lag_168h.

Kita butuh one week history dulu.

~~~text
Jan 1–7
→ warm-up

Jan 8 onward
→ complete model rows
~~~

Warm-up bukan waste.

Dia menyediakan context.

---

## Complete Zone-Hour Grid

Kalau di satu zone jam tertentu zero trip, groupby raw trips tidak produce row.

Tapi zero demand itu valid information.

Jadi kita build complete grid:

~~~text
all Manhattan zones
×
24 hours
~~~

Missing combination fill:

~~~text
trip_count = 0
~~~

Kenapa penting?

Karena time series harus continuous.

Kalau row zero-demand hilang, model bisa mengira time jump.

---

## zone_id categorical

Zone ID adalah identifier.

~~~text
zone 200
~~~

bukan “dua kali lebih besar” daripada zone 100.

Jadi treat zone sebagai categorical feature.

Ini small modeling detail tapi conceptually correct.

---

## Model choice

Main model:

~~~text
HistGradientBoostingRegressor
~~~

Kenapa?

- tabular-friendly,
- CPU-friendly,
- relatively fast,
- no GPU,
- supports categorical handling,
- easy serving.

Workshop focus MLOps, bukan model architecture competition.

Kalau model terlalu heavy, peserta habis waktu nunggu training.

---

## Time-based split

Jangan random split.

Kenapa?

Karena problem kita temporal.

Random split bisa bikin future patterns masuk training sementara earlier period jadi validation.

Lebih realistic:

~~~text
past
→ train

later period
→ validation
~~~

Initial:

~~~text
Jan 8–21 train
Jan 22–26 validation
~~~

Retraining:

~~~text
latest snapshot
↓
last 5 days validation
~~~

Validation ikut maju.

---

## Training-serving consistency

Training feature logic dan online serving feature logic harus punya same semantics.

Kalau training lag_24h benar, tapi serving lag_24h salah offset, production behavior rusak.

Makanya kita test exact feature values.

Ini alasan feature engineering bukan sekadar preprocessing detail. Ini production contract.

---

## Checkpoint

1. Lag feature itu apa?
2. Kenapa rolling harus shift dulu?
3. Kenapa group by zone?
4. Warm-up 7 hari muncul dari mana?
5. Kenapa zero-demand row harus tetap ada?
6. Kenapa random split kurang cocok?
7. Training-serving consistency artinya apa?
