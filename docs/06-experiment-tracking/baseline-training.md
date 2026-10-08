# Baseline Training — Sebelum MLOps Tools, Pastikan ML Workflow-nya Masuk Akal Dulu

Ada temptation di workshop MLOps:

> “Langsung buka MLflow, Airflow, Docker biar keren.”

Tapi kalau underlying ML workflow belum benar, kita cuma mengotomatisasi sesuatu yang belum kita pahami.

Jadi project ini sengaja punya fase **manual baseline training** dulu.

Kita ingin peserta merasakan:

- dataset input;
- time split;
- baseline;
- model;
- metric;
- local artifact.

Baru setelah pain point tracking/reproducibility muncul, DVC dan MLflow masuk.

---

## Dua comparator utama

Kita punya:

### Naive 24-hour baseline

~~~text
prediction(t)
=
demand(t - 24h)
~~~

Simple banget.

Tidak ada fit.

Tidak ada hyperparameter search.

Cuma:

> “Jam yang sama kemarin kira-kira jadi prediction hari ini.”

### HistGradientBoostingRegressor

Model tabular yang menggunakan:

- zone category;
- calendar features;
- lag features;
- rolling means.

---

## Kenapa baseline wajib?

Suppose main model:

~~~text
MAE = 10.2
~~~

Bagus nggak?

Tanpa context, kita nggak tahu.

Case A:

~~~text
baseline MAE = 8
model MAE = 10.2
~~~

Fancy model kalah.

Case B:

~~~text
baseline MAE = 15
model MAE = 10.2
~~~

Sekarang improvement meaningful.

Baseline memberi **minimum bar**.

---

## Analogi baseline

Kalian bikin route optimization AI.

Sebelum claim AI keren, compare dengan:

> “Ambil jalan terpendek dari Google Maps standard.”

Kalau AI justru lebih lambat, complexity belum justify.

Di taxi demand:

~~~text
yesterday same hour
~~~

adalah simple rule yang cukup masuk akal karena demand punya daily seasonality.

Jadi baseline bukan strawman sengaja jelek.

---

## Kenapa lag_24h jadi baseline?

Karena use case punya natural daily pattern.

Morning commute hari ini mungkin mirip morning commute kemarin.

Evening demand juga.

Baseline yang terlalu bodoh:

~~~text
always predict 0
~~~

mungkin mudah dikalahkan, tapi kurang useful.

Good baseline harus cukup reasonable sehingga model benar-benar harus earn improvement.

---

## Training snapshot

Manual training membaca:

~~~text
data/snapshots/training/taxi_demand_2025-01-26.csv
~~~

Kenapa snapshot, bukan moving feature file?

Karena training input harus jelas.

Kita ingin:

> “Model ini train dari data cutoff Jan 26.”

Bukan:

> “Model ini train dari whatever latest file saat command dijalankan.”

---

## Time-based split

Initial:

~~~text
Jan 8–21
→ train

Jan 22–26
→ validation
~~~

Kenapa tidak random split?

Time series punya order.

Production pattern:

~~~text
past
↓ train
future
↓ predict
~~~

Validation sebaiknya simulate itu.

Random split bisa menyebabkan:

~~~text
future-ish rows
→ training

older rows
→ validation
~~~

yang kurang realistis.

---

## Warm-up Jan 1–7

Kenapa snapshot historical mulai Jan 1 tapi training model-ready row baru Jan 8?

Karena:

~~~text
lag_168h
=
7-day history
~~~

Jan 1 target tidak punya previous-week value.

Jan 1–7 menjadi context.

Ini contoh kenapa:

~~~text
dataset history
≠
training target rows
~~~

Tidak semua row harus menjadi training example untuk tetap useful.

---

## Manual training flow

~~~text
load snapshot
↓
validate/sort timestamp
↓
split train and validation
↓
evaluate naive 24h baseline
↓
prepare model feature matrix
↓
train HGB
↓
predict validation
↓
calculate MAE + RMSE
↓
compare baseline vs model
↓
save local artifact + metrics
~~~

Perhatikan:

> Kita belum pakai MLflow.

Deliberate.

Biar nanti ketika MLflow masuk, participant ngerti problem yang dia solve.

---

## MAE intuition

MAE:

~~~text
mean(abs(prediction - actual))
~~~

Kalau:

~~~text
MAE = 10
~~~

roughly:

> model rata-rata meleset sekitar 10 pickups per zone-hour.

Easy to communicate.

---

## RMSE intuition

RMSE:

~~~text
sqrt(mean(error²))
~~~

Squaring membuat large errors dihukum lebih berat.

Misalnya dua model punya MAE mirip.

Model A error fairly consistent.

Model B punya beberapa massive misses.

RMSE Model B bisa lebih tinggi.

Jadi:

~~~text
MAE
→ typical absolute mistake

RMSE
→ more sensitive to big misses
~~~

---

## Kenapa primary metric MAE?

Karena interpretasi domain gampang.

Pickup count error directly understandable.

RMSE tetap dicatat sebagai secondary perspective.

Metric choice sebaiknya relate ke business/problem semantics, bukan cuma convention.

---

## Model matrix dan categorical zone

Sebelum fit, model input select feature columns.

zone_id diubah categorical.

Kenapa?

~~~text
zone 200
~~~

tidak mathematically dua kali zone 100.

Identifier bukan magnitude.

Kalau model treat numeric continuous, relation yang dipelajari bisa misleading.

---

## HGB parameter choice

Main config kurang lebih punya:

~~~text
learning_rate
max_iter
max_leaf_nodes
l2_regularization
random_state
~~~

Workshop tidak fokus exhaustive tuning.

Kenapa?

Karena learning objective utama MLOps lifecycle.

Kita butuh model yang:

- reasonably strong;
- CPU friendly;
- train cukup cepat;
- easy packaging;
- works well with tabular features.

HistGradientBoosting fit kebutuhan itu.

---

## “Kalau pakai model lebih canggih pasti lebih bagus dong?”

Belum tentu.

Chronos, LSTM, Transformer, XGBoost advanced tuning bisa dicoba sebagai experiment tambahan.

Tapi complexity membawa cost:

- dependency;
- compute;
- image size;
- inference latency;
- setup reliability;
- explanation overhead.

Workshop sengaja menggunakan model yang tidak menutupi lifecycle.

---

## Hyperparameter tuning di mana?

Bisa ditambahkan nanti.

Misalnya:

~~~text
learning_rate
max_leaf_nodes
l2
~~~

search beberapa combination.

MLflow cocok untuk compare runs.

Tapi tuning bukan syarat supaya MLOps valid.

MLOps mengelola lifecycle experiment/model, bukan hanya optimizer hyperparameter.

---

## Local artifact

Manual training save:

~~~text
models/taxi_demand_model.joblib
models/initial_metrics.json
~~~

Folder dibuat runtime dan ignored Git.

Kenapa model binary tidak di-commit?

Karena generated artifact punya lifecycle beda dari source code.

Nanti MLflow artifact store manage model secara lebih structured.

---

## Kenapa local artifact tetap ada kalau nanti MLflow?

Karena manual step punya pedagogical value.

Participant bisa lihat:

> “Oh, tanpa tracking tool kita memang akhirnya punya file model + metrics manual.”

Lalu MLflow masuk sebagai improvement.

Tool introduction jadi motivated.

---

## Model kalah baseline — apakah workshop gagal?

No.

Ini justru bisa jadi learning moment terbaik.

Jangan:

- invent metric;
- tweak validation sampai menang;
- leak target;
- hide result.

Healthy response:

1. verify data;
2. verify leakage;
3. verify split;
4. inspect feature;
5. tune reasonably;
6. accept baseline if still better.

Scientific honesty lebih penting dari demo narrative.

---

## “model_beats_baseline” sebagai gate

Later training pipeline compute boolean:

~~~text
model_mae < baseline_mae
~~~

Kalau false, candidate tidak didaftarkan sebagai challenger.

Ini mengubah baseline dari sekadar angka laporan menjadi **lifecycle guardrail**.

MLOps connects ML evaluation to operational decision.

---

## Reproducibility dan random_state

Model punya random_state.

Ini membantu repeated runs lebih deterministic.

Tapi random_state saja tidak guarantee byte-identical result across:

- different sklearn version;
- different low-level library;
- different CPU behavior.

Makanya environment versioning tetap relevant.

Reproducibility punya multiple layers.

---

## Jangan invent actual workshop metrics

Docs boleh kasih hypothetical example:

~~~text
baseline 15
model 10
~~~

untuk explain concept.

Tapi jangan claim:

> “Actual model kita MAE 10.”

kalau run real belum menghasilkan angka itu.

Presenter harus pakai observed run output.

Ini scientific integrity kecil tapi important.

---

## What if RMSE naik tapi MAE turun?

Interesting case.

Suppose candidate:

~~~text
MAE better
RMSE worse
~~~

Artinya average absolute error improve, tapi mungkin ada more extreme mistakes.

Apakah promote?

Tidak bisa dijawab dari satu metric saja.

Ini mengajarkan bahwa model selection bisa multi-objective.

Workshop gate sederhana pakai MAE baseline comparison, tapi reviewer tetap boleh inspect RMSE.

---

## Time split saat retraining

Initial split fixed by snapshot end.

Later retraining:

~~~text
last 5 days snapshot
→ validation
~~~

Jadi evaluation window ikut maju.

Kenapa?

Karena model baru harus diuji terhadap recent unseen period.

Baseline concept tetap sama.

---

## Checkpoint

Coba jawab:

1. Kenapa baseline wajib?
2. Kenapa lag_24h baseline cukup meaningful?
3. Kenapa random split kurang cocok?
4. Jan 1–7 role-nya apa?
5. MAE dan RMSE memberi perspective beda apa?
6. Kenapa zone_id categorical?
7. Kenapa HGB dipilih daripada langsung deep learning?
8. Local joblib artifact nanti digantikan responsibility-nya oleh apa?
9. Model kalah baseline, response sehat apa?
10. Kenapa random_state belum cukup untuk full reproducibility?
11. model_beats_baseline nanti dipakai di lifecycle bagian mana?
12. Kalau MAE turun tapi RMSE naik, kenapa decision belum otomatis obvious?

Kalau clear, kalian sudah punya ML evaluation foundation yang cukup kuat sebelum masuk DVC dan MLflow.
