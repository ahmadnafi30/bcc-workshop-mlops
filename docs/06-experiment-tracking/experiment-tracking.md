# MLflow Experiment Tracking

Sekarang kita sudah punya dua experiment yang meaningful:

```text
naive 24h
vs
HistGradientBoosting
```

Kalau cuma dua run, metric sebenarnya masih bisa dicatet manual. Tapi begitu kita mulai ubah hyperparameter, retrain model, ganti dataset snapshot, atau compare beberapa candidate model, file JSON mulai susah dipakai buat tracking.

Di sini MLflow mulai masuk.

## Start MLflow server

Dari root repository, buka terminal baru:

```bash
uv run mlflow server
```

Default local server bisa dibuka di:

```text
http://127.0.0.1:5000
```

Untuk workshop lokal, default SQLite backend dari MLflow sudah cukup. Nanti pas masuk Docker kita pindahin service ini ke container supaya setup-nya lebih konsisten.

## Run experiment

Pastikan feature dataset sudah ada:

```bash
uv run python scripts/bootstrap_data.py
uv run python scripts/prepare_historical_demand.py
uv run python scripts/build_features.py
uv run dvc repro create_training_snapshot
```

Lalu:

```bash
uv run python scripts/train_with_mlflow.py
```

Script ini bikin dua run di experiment:

```text
taxi-demand-forecasting

├── naive-24h
└── hist-gradient-boosting
```

## Apa yang ditrack?

Baseline punya:

```text
params
- model_type
- forecast_horizon
- train_rows
- validation_rows
- dataset_snapshot
- dataset_sha256
- dataset_rows

metrics
- mae
- rmse
```

Gradient boosting punya tambahan model config:

```text
learning_rate
max_iter
max_leaf_nodes
l2_regularization
random_state
```

dan model artifact yang bisa dipakai lagi tanpa train ulang.

## Kenapa baseline ikut MLflow?

Karena baseline adalah bagian dari experiment comparison.

Di MLflow UI kita pengen bisa lihat:

```text
Run                         MAE       RMSE
------------------------------------------------
naive-24h                   ...       ...
hist-gradient-boosting      ...       ...
```

Jadi pertanyaan kita bukan cuma:

> model mana yang metric-nya paling bagus?

tapi:

> apakah ML model ini benar-benar kasih improvement dibanding rule sederhana?

## Model artifact

Untuk gradient boosting, MLflow juga nyimpen model dengan nama artifact:

```text
model
```

Script bakal print URI seperti:

```text
runs:/<run-id>/model
```

URI ini penting karena next step kita bisa mengambil model dari sebuah run lalu masukin ke **Model Registry**.

## Tracking vs Registry

Dua konsep ini jangan dicampur.

**Experiment Tracking** jawab:

```text
apa yang kita coba?
param-nya apa?
metric-nya berapa?
artifact-nya di mana?
```

Sedangkan **Model Registry** jawab:

```text
model mana yang sekarang jadi candidate?
model version berapa?
model mana yang jadi champion?
```

Jadi kita tracking dulu, baru model yang memang layak kita register.
