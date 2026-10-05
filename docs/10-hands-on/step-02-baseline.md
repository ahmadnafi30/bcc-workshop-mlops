# Step 2 — Feature Engineering + Baseline: Jangan MLOps-in Model yang Belum Jelas

Sekarang kita punya hourly demand.

Before DVC, MLflow, dan Airflow, kita harus punya **ML workflow yang benar**.

Kenapa?

Karena MLOps bukan pengganti Machine Learning fundamentals.

Kalau feature leakage, orchestration yang bagus cuma automate leakage lebih cepat. 😭

---

## Goal

Setelah step ini:

- model-ready feature table terbentuk,
- kalian ngerti lag dan rolling features,
- leakage rule jelas,
- training snapshot manual dibuat,
- baseline dan main model dibandingkan.

---

## 1. Build features

~~~bash
uv run python scripts/build_features.py
~~~

Output:

~~~text
data/features/taxi_demand_features.parquet
~~~

---

## 2. Inspect columns

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/features/taxi_demand_features.parquet'); print(df.columns.tolist()); print(df.head())"
~~~

Cari:

~~~text
hour
day_of_week
is_weekend
lag_1h
lag_24h
lag_168h
rolling_mean_3h
rolling_mean_24h
target_trip_count
~~~

---

## 3. Pause: leakage check

Ambil satu target row.

Misalnya:

~~~text
target = Jan 10 18:00
~~~

Tanya:

> “Kalau feature ini digunakan, apakah nilainya sudah diketahui sebelum jam 18:00?”

Kalau tidak, leakage.

---

## 4. Kenapa rolling mean shift dulu?

Misalnya rolling 3h.

Bad:

~~~text
16:00
17:00
18:00 actual
~~~

Target leaked.

Correct:

~~~text
15:00
16:00
17:00
~~~

atau previous three hours sesuai implementation.

Jadi shift dulu, baru rolling.

---

## 5. Create initial snapshot

~~~bash
uv run python scripts/create_training_snapshot.py --cutoff-date 2025-01-26
~~~

Output:

~~~text
data/snapshots/training/taxi_demand_2025-01-26.parquet
~~~

Kenapa snapshot sekarang?

Karena feature dataset akan terus tumbuh.

Training butuh frozen input identity.

---

## 6. Train manually

~~~bash
uv run python scripts/train_model.py
~~~

Kalian akan lihat:

- baseline MAE/RMSE,
- model MAE/RMSE,
- row counts.

---

## 7. Jangan langsung lihat “model bagus”

Pertanyaan pertama:

> “Main model beat baseline nggak?”

Kalau iya, good.

Kalau nggak, itu bukan kegagalan workshop.

Itu finding.

ML yang sehat nggak memaksa fancy model selalu menang.

---

## 8. Baseline intuition

Naive:

~~~text
prediction today 18:00
=
yesterday 18:00
~~~

Taxi demand punya daily cycle, jadi baseline reasonable.

Ini jauh lebih meaningful daripada baseline random.

---

## 9. Time split

Kenapa tidak random?

Karena target production ada di future.

Time split mimic:

~~~text
learn from past
↓
validate on later period
~~~

Random split bisa mix time context.

---

## 10. Inspect local artifact

Generated:

~~~text
models/
~~~

Kenapa folder nggak ada permanent placeholder lagi?

Karena script create runtime folder saat dibutuhkan.

Generated artifact tidak perlu dipaksa exist di source repo.

---

## Mini challenge

### Question A

Kalau lag_24h model sangat kuat, apa artinya?

Ada strong daily seasonality.

### Question B

Kalau model beat baseline by 0.01 MAE tapi jauh lebih complex, apakah automatically worth it?

Belum tentu.

Complexity vs gain harus dipikirkan.

---

## Checkpoint

Kalian harus bisa explain:

- target,
- lags,
- rolling,
- leakage,
- warm-up,
- time split,
- baseline,
- model comparison.

Baru setelah itu kita version data snapshot dengan DVC.
