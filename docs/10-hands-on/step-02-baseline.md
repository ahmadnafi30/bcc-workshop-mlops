# Step 2 — Features & Baseline: Sebelum Pakai Banyak Tools, Pastikan Model Kita Punya Fondasi yang Sehat

Sekarang kita punya hourly demand history.

Belum ada MLflow.

Belum ada Airflow.

Belum ada model registry.

Bagus.

Kita sengaja belajar ML workflow-nya dulu.

Kalau model, split, atau feature engineering salah, MLOps tools hanya akan membuat kesalahan itu lebih otomatis. 😭

---

## Goal

Di akhir step ini kalian harus bisa:

- build feature dataset;
- explain lag/rolling features;
- identify leakage;
- create initial training snapshot;
- train naive baseline + HGB;
- read MAE/RMSE;
- decide apakah main model benar-benar beat baseline;
- ngerti kenapa time split chronological.

---

## 1. Build features

Run:

~~~bash
uv run python scripts/build_features.py
~~~

Output:

~~~text
data/features/taxi_demand_features.parquet
~~~

---

## 2. Inspect columns

Try:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/features/taxi_demand_features.parquet'); print(df.columns.tolist()); print(df.head())"
~~~

Cari:

~~~text
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

---

# 3. Jangan cuma lihat nama column — derive satu row manual

Ambil target:

~~~text
Jan 26 18:00
zone tertentu
~~~

Coba cari processed demand:

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
16:00
15:00
yesterday 18:00
last week 18:00
~~~

Lalu compare dengan lag columns.

Kalau manual derivation match, feature semantics lebih tangible.

---

# 4. Leakage check

Pertanyaan untuk setiap feature:

> “Apakah value ini sudah known sebelum target hour terjadi?”

Allowed:

~~~text
target hour calendar info
past demand
past rolling average
~~~

Not allowed:

~~~text
actual target demand
future demand
rolling window containing target
~~~

Ini rule sederhana yang harus terus dibawa sampai serving.

---

# 5. Kenapa rolling shift dulu?

Target 18:00.

rolling_mean_3h harus:

~~~text
15:00
16:00
17:00
~~~

Kalau include 18:00, model dapat answer sebagian.

Validation metric bisa kelihatan amazing.

Itu bukan model pintar.

Itu leakage.

---

# 6. Warm-up rows hilang setelah build features

Karena lag_168h perlu one-week history.

Coba inspect minimum timestamp feature dataset.

Expected sekitar Jan 8.

Ini bukan bug.

History Jan 1–7 dipakai sebagai context.

---

# 7. Kenapa zone_id category?

ID:

~~~text
100
200
~~~

tidak berarti zone 200 dua kali lebih besar dari zone 100.

Identifier harus diperlakukan sebagai category.

Ini modeling semantics, bukan formatting.

---

# 8. Create initial training snapshot

Run:

~~~bash
uv run python scripts/create_training_snapshot.py --cutoff-date 2025-01-26
~~~

Output:

~~~text
data/snapshots/training/taxi_demand_2025-01-26.parquet
~~~

Kenapa snapshot sekarang?

Karena kita ingin training input frozen.

Step 3 nanti DVC formalize reproducibility-nya.

---

# 9. Inspect snapshot range

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/snapshots/training/taxi_demand_2025-01-26.parquet'); print(df['timestamp'].min()); print(df['timestamp'].max()); print(df.shape)"
~~~

Question:

> “Apakah Jan 27 boleh masuk?”

No.

Initial model cutoff Jan 26.

---

# 10. Time split

Training code secara dynamic mengambil last 5 days snapshot sebagai validation.

Untuk initial snapshot:

~~~text
Jan 8–21
→ train

Jan 22–26
→ validation
~~~

Kenapa time split?

Karena deployment juga selalu:

~~~text
past
→ learn

future
→ predict
~~~

Random split kurang realistic untuk forecasting.

---

# 11. Baseline prediction

Naive baseline:

~~~text
prediction
=
lag_24h
~~~

Artinya target jam 18:00 pakai demand kemarin jam 18:00.

No fit.

No hyperparameter.

Simple.

---

# 12. Sebelum train main model, predict expectation

Question:

> “Kalau taxi demand punya strong daily seasonality, apakah baseline ini bisa cukup kuat?”

Yes.

Makanya baseline meaningful.

Kalau main model tidak beat baseline, itu possible.

Jangan assume ML selalu menang.

---

# 13. Run manual training

~~~bash
uv run python scripts/train_model.py
~~~

Terminal print:

~~~text
naive MAE
naive RMSE
model MAE
model RMSE
model artifact path
metrics path
~~~

Read actual numbers.

Docs tidak akan claim exact metric karena result harus berasal dari run kalian.

---

# 14. MAE

Suppose hypothetical:

~~~text
MAE = 10
~~~

Interpretasi:

> model rata-rata absolute error sekitar 10 pickups per zone-hour.

Gampang communicate.

---

# 15. RMSE

RMSE lebih punish big misses.

Suppose:

~~~text
Model A
errors mostly 8–12

Model B
mostly 5
but some errors 80
~~~

MAE mungkin tidak terlalu jauh.

RMSE Model B bisa spike.

Jadi RMSE bantu lihat tail error severity.

---

# 16. Model vs baseline decision

Case hypothetical:

~~~text
baseline MAE = 14
model MAE = 10
~~~

Main model improves.

Case:

~~~text
baseline MAE = 9
model MAE = 10
~~~

Main model kalah.

Apa yang dilakukan?

Healthy process:

1. verify feature correctness;
2. verify split;
3. inspect leakage;
4. inspect data;
5. tune reasonably;
6. accept result.

Jangan manipulate validation supaya model menang.

---

# 17. Local artifacts

Manual script save:

~~~text
models/taxi_demand_model.joblib
models/initial_metrics.json
~~~

Kenapa useful?

Participant bisa lihat pain point manual tracking.

Kalau experiment kedua datang, kita mulai punya:

~~~text
model file
metrics file
which one belongs together?
~~~

MLflow nanti solve ini.

---

# 18. Inspect metrics JSON

Open:

~~~text
models/initial_metrics.json
~~~

Coba compare baseline/model values.

Question:

> “Kalau besok train lagi, file ini overwrite nggak?”

Potentially yes.

Nah, itu salah satu motivation experiment tracking.

---

# 19. Why HistGradientBoosting?

Bukan karena objectively best taxi model di dunia.

Dipilih karena:

- tabular-friendly;
- CPU-friendly;
- training cukup cepat;
- dependency ringan;
- supports categorical feature;
- easy serving;
- workshop time reasonable.

Model choice dipengaruhi learning objective dan operational constraints.

---

# 20. Kenapa bukan LSTM/Chronos core?

Advanced forecasting model bisa dicoba.

Tapi kalau model membutuhkan huge download/GPU/complex serving, participant bisa habis waktu di environment issue.

Core workshop ingin lifecycle visible.

Model sophistication adalah extension.

---

# 21. Mini exercise: compare metrics

Suppose:

~~~text
baseline:
MAE 12
RMSE 20

model:
MAE 10
RMSE 25
~~~

Apakah model clearly better?

Not fully obvious.

Average absolute error improve, but large misses worse.

Ini menunjukkan single metric tidak selalu enough untuk real governance.

Workshop gate utama MAE, reviewer tetap inspect RMSE.

---

# 22. Run tests

~~~bash
uv run pytest
~~~

Feature tests penting karena leakage bug kadang tidak crash.

Code bisa run perfectly sambil semantically wrong.

Testing target harus include known failure modes.

---

# 23. What if actual model loses?

Workshop tetap valid.

MLOps lifecycle tidak require main model selalu superior.

Justru experiment tracking + registry membantu manage evidence.

Candidate yang jelek bisa tercatat tanpa dipromote.

Itu normal science.

---

# 24. Checkpoint

Pastikan ada:

~~~text
data/features/taxi_demand_features.parquet
✅

data/snapshots/training/taxi_demand_2025-01-26.parquet
✅

models/taxi_demand_model.joblib
✅

models/initial_metrics.json
✅
~~~

Lalu explain:

1. Lag 1h/24h/168h artinya apa?
2. Kenapa rolling shift dulu?
3. Warm-up rows role-nya apa?
4. zone_id kenapa categorical?
5. Kenapa snapshot cutoff Jan 26?
6. Kenapa split chronological?
7. Baseline lag_24h kenapa meaningful?
8. MAE vs RMSE?
9. Model kalah baseline apakah pipeline gagal?
10. Kenapa manual local artifacts mulai painful setelah banyak experiment?
11. Kenapa model yang lebih advanced tidak otomatis lebih suitable buat workshop?
12. Apa failure mode yang test feature seharusnya catch?

Kalau clear, next kita formalize data reproducibility dengan DVC.
