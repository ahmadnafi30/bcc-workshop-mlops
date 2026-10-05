# Step 2 — Feature Engineering and Baseline Model

Sekarang kita punya hourly demand.

Next question:

> “Gimana caranya model memanfaatkan history buat predict satu jam ke depan?”

Di step ini kita build features dan train model pertama **tanpa MLflow dulu**.

Kenapa tanpa MLflow?

Supaya kita tahu normal ML workflow-nya dulu.

---

# Target step

Setelah selesai:

- feature dataset ada,
- training snapshot ada,
- naive baseline dievaluasi,
- HistGradientBoosting ditrain,
- kalian ngerti leakage protection.

---

# 1. Build features

~~~bash
uv run python scripts/build_features.py
~~~

Output:

~~~text
data/features/taxi_demand_features.parquet
~~~

---

# 2. Inspect feature columns

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/features/taxi_demand_features.parquet'); print(df.columns.tolist()); print(df.head())"
~~~

Kalian akan lihat feature seperti:

~~~text
hour
day_of_week
is_weekend
lag_1h
lag_24h
lag_168h
rolling_mean_3h
...
target_trip_count
~~~

---

# 3. Coba verify satu row secara manual

Ambil satu zone dan timestamp.

Tanya:

> Kalau target jam 18:00, lag_1h berasal dari jam berapa?

Expected:

~~~text
17:00
~~~

lag_24h?

~~~text
yesterday 18:00
~~~

lag_168h?

~~~text
same hour one week earlier
~~~

---

# 4. Leakage check

Ini jangan dilewati.

Rolling feature kita dibuat dari:

~~~text
shift(1)
then
rolling()
~~~

Kenapa?

Karena target hour actual tidak boleh masuk feature.

Coba bayangin kalau current target ikut.

Metric bisa dramatically bagus.

Tapi production impossible.

---

# 5. Build training snapshot manual

~~~bash
uv run python scripts/create_training_snapshot.py   --cutoff-date 2025-01-26
~~~

Output:

~~~text
data/snapshots/training/
taxi_demand_2025-01-26.parquet
~~~

Kenapa snapshot?

Karena live feature file terus berubah saat Jan 27, Jan 28 masuk.

Training input harus frozen.

---

# 6. Train model

~~~bash
uv run python scripts/train_model.py
~~~

Kalian akan lihat result baseline dan main model.

Jangan langsung tutup terminal setelah selesai.

Read numbers.

---

# 7. Compare baseline

Naive prediction:

~~~text
prediction(t)
=
lag_24h
~~~

Kalau model utama:

~~~text
MAE lower than baseline
~~~

bagus.

Kalau lebih tinggi:

> ML model belum justify complexity.

Dan itu valid outcome.

---

# 8. Jangan invent metric

Metric actual tergantung run/data.

Docs tidak kasih fake expected MAE.

Kenapa?

Karena kita mau peserta percaya output real, bukan mencari angka yang “harus cocok”.

Yang penting relation:

~~~text
baseline
vs
model
~~~

---

# 9. Inspect local artifacts

Setelah training:

~~~text
models/
taxi_demand_model.joblib
initial_metrics.json
~~~

Ini temporary manual artifact path.

Nanti MLflow replace manual bookkeeping.

---

# 10. Think like reviewer

Coba jawab:

### Model metric jauh terlalu bagus, first suspicion apa?

~~~text
data leakage
~~~

### Kenapa random split kurang ideal?

~~~text
time order bisa bocor / tidak mimic future
~~~

### Kenapa zone_id categorical?

~~~text
ID bukan numeric magnitude
~~~

---

# Mini challenge

Kalau:

~~~text
baseline MAE = 9
model MAE = 11
~~~

Apakah kita register model sebagai challenger?

Dalam project logic:

~~~text
no
~~~

Karena main model gagal beat simple baseline.

---

# Checkpoint

Kalian siap lanjut kalau bisa explain:

- feature lag,
- rolling,
- leakage,
- time split,
- baseline.

Next kita masuk DVC dan mulai membahas reproducibility.
