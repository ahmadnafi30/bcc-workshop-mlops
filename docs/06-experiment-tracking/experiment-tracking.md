# MLflow Tracking — Experiment Notebook yang Nggak Mengandalkan Ingatan

## Satu run masih gampang

Misalnya:

~~~text
Run 1
MAE = 10.8
~~~

Besok:

~~~text
Run 2
learning_rate = 0.05
MAE = 10.2
~~~

Lusa:

~~~text
Run 3
max_iter changed
MAE = 10.4
~~~

Setelah 20 run:

> “Yang 10.2 itu snapshot apa ya?”

> “Param-nya apa?”

> “Model artifact-nya yang mana?”

Inilah pain yang MLflow Tracking solve.

---

# MLflow Tracking itu apa?

Satu experiment execution dicatat sebagai **run**.

Run bisa punya:

~~~text
parameters
metrics
tags
artifacts
dataset metadata
run ID
~~~

Jadi terminal output berubah menjadi structured experiment record.

---

# Analogi: laboratory notebook

Researcher tidak hanya menulis:

~~~text
result bagus
~~~

Dia catat:

- sample,
- setup,
- condition,
- measurement,
- result.

MLflow kurang lebih seperti lab notebook untuk ML experiments.

---

# Start MLflow

~~~bash
uv run python scripts/start_mlflow.py
~~~

UI:

~~~text
http://127.0.0.1:5000
~~~

Workshop helper menyimpan state ke:

~~~text
.mlflow/
~~~

Folder ini juga dipakai Compose nanti.

Jadi local experiment history dan Registry state tetap nyambung.

---

# Tracking URI

Training code perlu tahu server address.

Lokal:

~~~text
http://127.0.0.1:5000
~~~

Dalam Docker:

~~~text
http://mlflow:5000
~~~

Same service concept.

Different network perspective.

---

# Experiment

MLflow experiment adalah grouping run.

Project kita punya experiment taxi demand forecasting.

Di dalamnya ada baseline run dan model runs.

---

# Run

Satu training execution = satu run.

Kita log dua run initial:

~~~text
naive-24h
hist-gradient-boosting
~~~

Kenapa baseline dilog juga?

Karena comparison context harus persisted.

Kalau hanya model utama yang tersimpan, evidence “kenapa model ini worth it” hilang.

---

# Parameters

Parameter = configuration/input.

Contoh:

~~~text
learning_rate
max_iter
model_type
dataset_snapshot
train_rows
validation_rows
~~~

Pertanyaan yang dijawab:

> Experiment dijalankan dengan setting apa?

---

# Metrics

Metric = measured output.

~~~text
mae
rmse
~~~

Pertanyaan:

> Hasilnya bagaimana?

---

# Tags

Tag = descriptive context.

Contoh:

~~~text
task
model_family
stage
~~~

Useful buat search/filter.

---

# Artifacts

Model juga dilog sebagai MLflow artifact.

Ini lebih structured daripada random file:

~~~text
model_final_bener.joblib
~~~

Artifact linked ke run.

---

# Run ID

Setiap run punya unique ID.

Nanti Registry model version reference source run.

Chain:

~~~text
model version
↓
run ID
↓
metrics
params
artifact
dataset fingerprint
~~~

---

# Dataset fingerprint

Snapshot kita calculate SHA256.

Logged metadata:

~~~text
dataset_snapshot
dataset_sha256
dataset_rows
dataset_zones
~~~

Kenapa hash penting?

Filename alone nggak guarantee content sama.

Hash membantu identify content.

---

# Run tracked training

~~~bash
uv run python scripts/train_with_mlflow.py
~~~

Expected:

~~~text
baseline run
model run
metric comparison
~~~

---

# Explore UI

Jangan cuma lihat table summary.

Open run.

Cari:

### Parameters

Model setting.

### Metrics

MAE/RMSE.

### Tags

Stage.

### Artifacts

Saved model.

### Run ID

Lineage reference.

---

# Compare runs

MLflow UI bisa compare side-by-side.

Misalnya:

~~~text
Run A
MAE 10.8

Run B
MAE 10.2

Run C
MAE 10.5
~~~

Sekarang param difference lebih gampang dilihat.

---

# MLflow Tracking vs Registry

Jangan campur.

~~~text
Tracking
→ what experiments happened?

Registry
→ which model versions are managed candidates?
~~~

Most runs mungkin never masuk Registry.

Itu normal.

---

# MLflow vs DVC

Juga beda.

~~~text
DVC
→ reproduce data artifact state

MLflow
→ record experiment context + result
~~~

Mereka complement.

---

# Workshop takeaway

Sebelum MLflow:

> “Kayaknya run kemarin paling bagus.”

Setelah MLflow:

> “Run abc memakai snapshot SHA xyz, learning_rate 0.05, validation MAE 10.2, dan artifact model ini.”

Much better.


---

# Implementation Deep Dive — Logging One MLflow Run

Project kita secara concept melakukan:

~~~python
with mlflow.start_run(
    run_name="hist-gradient-boosting"
) as run:

    mlflow.log_params(
        {
            "model_type": "hist_gradient_boosting",
            "learning_rate": 0.05,
            "dataset_snapshot": "...",
            "dataset_sha256": "...",
        }
    )

    mlflow.log_metrics(
        {
            "mae": ...,
            "rmse": ...,
        }
    )

    mlflow.set_tags(
        {
            "task": "taxi-demand-forecasting",
            "stage": "validation",
        }
    )

    mlflow.sklearn.log_model(
        sk_model=model,
        name="model",
        input_example=example,
    )
~~~

## start_run

Membuka context satu run.

## log_params

Configuration/input.

## log_metrics

Measured numeric result.

## set_tags

Searchable/descriptive context.

## log_model

Store model artifact dalam MLflow model format.

## Kenapa input_example?

MLflow bisa menyimpan contoh input dan infer signature.

Model artifact jadi lebih inspectable daripada binary opaque saja.

---

# Kalau design tracking sendiri

Jangan log everything random.

Tanya:

~~~text
Apa yang dibutuhkan buat compare run?
Apa yang dibutuhkan buat trace data?
Apa artifact yang perlu disimpan?
Apa context yang useful buat filter?
~~~

Logging yang purposeful lebih valuable daripada metadata banyak tapi nggak jelas gunanya.
