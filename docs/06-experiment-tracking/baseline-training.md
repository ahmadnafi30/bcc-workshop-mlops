# Baseline Training — Sebelum Experiment Tracking

## Kenapa kita sengaja mulai manual?

Kalau dari awal semua experiment sudah otomatis tercatat, kita nggak pernah merasakan kenapa tracking dibutuhkan.

Jadi first model run kita sederhana.

~~~text
load snapshot
↓
split by time
↓
baseline
↓
train model
↓
evaluate
↓
save artifact locally
~~~

---

# Input: training snapshot

File:

~~~text
data/snapshots/training/
taxi_demand_2025-01-26.parquet
~~~

Kenapa snapshot, bukan live feature file?

Karena snapshot frozen.

Live features terus berubah seiring replay.

Training input harus traceable.

---

# Chronological split

Initial:

~~~text
Jan 8–21
train

Jan 22–26
validation
~~~

Kenapa time split?

Model production akan menghadapi future.

Validation seharusnya mimic itu.

Random split bisa mix older/future pattern dengan cara yang kurang realistic.

---

# Naive baseline

Rule:

~~~text
prediction
=
lag_24h
~~~

Jadi target Jan 25 18:00 diprediksi dengan Jan 24 18:00 demand.

No model.fit().

Simple domain heuristic.

---

# Main model

~~~text
HistGradientBoostingRegressor
~~~

Kenapa ini cocok?

- strong tabular model,
- train cepat,
- no GPU,
- serving ringan.

Hyperparameter seperti:

~~~text
learning_rate
max_iter
max_leaf_nodes
l2_regularization
~~~

---

# Run

~~~bash
uv run python scripts/train_model.py
~~~

Output console akan compare baseline vs model.

---

# Metrics

Primary:

~~~text
MAE
~~~

Secondary:

~~~text
RMSE
~~~

Yang kita lihat:

> Model beat baseline nggak?

Bukan hanya:

> Model berhasil train nggak?

---

# Local artifacts

Script manual bisa save:

~~~text
models/taxi_demand_model.joblib
models/initial_metrics.json
~~~

Folder ini runtime-generated dan ignored.

Ini cukup untuk first experiment.

Tapi setelah run makin banyak, file naming manual mulai messy.

---

# Think like a reviewer

Kalau metric tiba-tiba extremely bagus, jangan langsung senang.

Ask:

- leakage?
- split benar?
- target accidentally masuk feature?
- row count masuk akal?

Good MLOps tidak hanya automate success.

Good MLOps juga make suspicious result easier to investigate.

---

# Pain point yang kita bawa ke MLflow

Setelah beberapa run, kita butuh jawab:

~~~text
Which params?
Which snapshot?
Which metric?
Which model artifact?
Which run?
~~~

Dan jawaban itu tidak seharusnya bergantung ke ingatan presenter.

Next: MLflow Tracking.
