# Baseline Training — Sebelum Tools MLOps, Kita Harus Punya ML Workflow yang Benar Dulu

Ada temptation kalau workshop MLOps:

> Langsung buka MLflow, Airflow, Docker.

Padahal itu bikin tools jadi abstrak.

Jadi kita sengaja build model secara manual dulu.

Biar peserta punya pain point nyata sebelum tooling masuk.

---

## Dua model yang dibandingkan

### Naive 24-hour baseline

Rule:

~~~text
prediction(t)
=
demand(t - 24h)
~~~

No fitting.

No fancy hyperparameter.

Cuma yesterday same hour.

### HistGradientBoostingRegressor

Main model pakai:

- calendar feature,
- zone category,
- lags,
- rolling means.

---

## Kenapa baseline bukan optional?

Tanpa baseline, MAE 10.2 terlihat bagus atau jelek?

Kita nggak punya context.

Kalau baseline 8:

~~~text
main model = 10.2
baseline = 8
~~~

Main model worse.

Kalau baseline 15:

~~~text
main model = 10.2
baseline = 15
~~~

Now improvement meaningful.

Baseline bikin complexity accountable.

---

## Time split

Kita nggak random split.

Initial:

~~~text
Jan 8–21
train

Jan 22–26
validation
~~~

Kenapa chronological?

Karena production prediction selalu future relatif ke training history.

Random split bisa blur temporal boundary.

---

## Kenapa Jan 1–7 nggak train?

Because lag_168h.

Row Jan 1 tidak punya data one week before.

Jan 1–7 provide warm-up history.

Feature complete mulai Jan 8.

---

## Model training flow

~~~text
load snapshot
↓
time split
↓
evaluate naive baseline
↓
prepare model matrix
↓
train HGB
↓
predict validation
↓
MAE / RMSE
↓
compare
↓
save local artifact
~~~

Notice MLOps belum masuk.

Ini deliberate.

---

## Local artifact

Manual path bisa save:

~~~text
models/taxi_demand_model.joblib
models/initial_metrics.json
~~~

Kenapa folder models nggak committed?

Generated model binary bukan source code.

Nanti MLflow artifact store jadi management layer yang lebih appropriate.

---

## Metrics jangan invented

Salah satu rule docs/project:

> Jangan tulis angka performance actual kalau belum benar-benar dijalankan.

Kenapa?

Karena dataset, environment, code bisa berubah.

Workshop presenter harus run pipeline dan use observed metrics.

Ini juga scientific honesty.

---

## Model kalah baseline gimana?

Ini interesting.

Jangan “fix” metric cuma supaya demo kelihatan bagus.

Kalau model kalah:

1. inspect feature quality,
2. check leakage or split,
3. tune model reasonably,
4. accept baseline if still better.

MLOps bukan tentang memaksa fancy model menang.

---

## Why HGB?

HistGradientBoosting dipilih karena:

- fast enough,
- tabular,
- CPU friendly,
- sklearn ecosystem,
- easy serving.

Kita deliberately tidak pilih deep learning supaya workshop focus ke lifecycle.

---

## Reproducibility seeds

Model punya random_state.

Kenapa?

Supaya run lebih deterministic.

Tapi full reproducibility tetap bisa dipengaruhi library version/hardware.

Makanya environment tracking tetap penting.

---

## Checkpoint

1. Kenapa baseline wajib?
2. Kenapa time split?
3. Warm-up period dari mana?
4. Kalau main model kalah baseline, response yang sehat apa?
5. Kenapa local model artifact bukan source code?
