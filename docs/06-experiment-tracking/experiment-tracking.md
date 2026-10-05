# MLflow Tracking — Biar Experiment Kita Nggak Cuma Hidup di Ingatan

Sekarang kita punya baseline dan main model.

Awalnya mungkin cuma dua run.

Masih gampang diingat.

Tapi bayangin nanti:

~~~text
run 1
run 2
run 3
run 4
...
run 37
~~~

Ada feature change, parameter change, snapshot baru, retraining.

Kalau tracking-nya cuma:

~~~text
notes.txt
model_final.joblib
model_final_bener.joblib
model_final_bener_fix.joblib
~~~

chaos tinggal tunggu waktu. 😭

MLflow Tracking masuk buat bikin experiment history lebih structured.

---

## Analogi: laboratory notebook

Scientist yang serius nggak cuma bilang:

> “Kemarin eksperimen saya bagus.”

Dia catat:

- sample,
- condition,
- procedure,
- measurement,
- result.

MLflow kurang lebih jadi laboratory notebook untuk ML experiments.

Satu experiment run punya context yang bisa dilihat lagi nanti.

---

## Experiment dan Run

### Experiment

Grouping logical.

Project kita punya experiment taxi demand forecasting.

Di dalamnya ada banyak run.

### Run

Satu execution training/evaluation.

Misalnya:

~~~text
naive-24h
hist-gradient-boosting
retraining-run-february
~~~

Setiap run punya unique ID.

---

## Apa yang kita log?

Ada empat kategori utama.

### Parameters

Input/configuration.

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

> “Run ini dijalankan dengan setting apa?”

### Metrics

Measured result.

~~~text
mae
rmse
~~~

Pertanyaan:

> “Hasilnya bagaimana?”

### Tags

Descriptive metadata.

~~~text
task
model_family
stage
~~~

Useful buat filter/search.

### Artifacts

File hasil run.

Model artifact, plot, report, atau file lain.

Project kita log model sklearn sebagai artifact.

---

## Kenapa baseline juga dilog?

Karena baseline adalah comparison context.

Kalau kita cuma log main model:

~~~text
MAE = 10.2
~~~

kita tahu nilainya, tapi nggak tahu apakah itu actually bagus dibanding simple rule.

Dengan baseline:

~~~text
naive MAE = 13.5
model MAE = 10.2
~~~

sekarang ada evidence bahwa model memberi improvement.

---

## Start MLflow

Workshop helper:

~~~bash
uv run python scripts/start_mlflow.py
~~~

UI:

~~~text
http://127.0.0.1:5000
~~~

State disimpan ke:

~~~text
.mlflow/
~~~

Kenapa helper custom?

Supaya local MLflow dan Docker Compose MLflow share state directory yang sama.

Jadi setelah kalian register champion locally, pindah ke Compose tidak tiba-tiba registry kosong.

Ini hasil audit workshop flow yang penting banget.

---

## Tracking URI

Application perlu tahu MLflow server ada di mana.

Local:

~~~text
http://127.0.0.1:5000
~~~

Docker:

~~~text
http://mlflow:5000
~~~

Same logical service, different network context.

---

## Actual logging pattern

Conceptually code kita melakukan:

~~~python
with mlflow.start_run(run_name="hist-gradient-boosting"):

    mlflow.log_params(
        {
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

Sekarang kita bedah.

### start_run

Buka satu experiment run context.

### log_params

Simpan configuration.

### log_metrics

Simpan numeric result.

### set_tags

Simpan descriptive context.

### log_model

Simpan model artifact dengan MLflow model packaging.

---

## Dataset lineage di MLflow

Kita log:

~~~text
dataset_snapshot
dataset_sha256
dataset_rows
dataset_zones
~~~

Kenapa?

Supaya run tidak cuma bilang:

> “Saya punya MAE 10.2.”

tapi:

> “Saya punya MAE 10.2 dari snapshot X dengan hash Y.”

Itu jauh lebih traceable.

---

## Run ID

Run ID adalah unique identifier.

Nanti saat model masuk Registry, model version bisa point ke source run.

Chain:

~~~text
registered model version
↓
source run ID
↓
metrics
parameters
dataset fingerprint
artifact
~~~

Ini lineage.

---

## Tracking vs Registry

Jangan campur.

### Tracking

Pertanyaan:

> “Experiment apa saja yang terjadi?”

### Registry

Pertanyaan:

> “Model version mana yang kita manage sebagai candidate/production?”

Most experiment runs tidak harus masuk Registry.

Itu normal.

Kita bisa punya 100 experiments, tapi cuma 3 model version yang dianggap layak candidate.

---

## MLflow vs DVC

Juga beda.

~~~text
DVC
→ reproduce data artifact

MLflow
→ record experiment context + result
~~~

Mereka complement.

---

## Input example dan signature

Saat log model, MLflow bisa simpan contoh input dan model signature.

Kenapa useful?

Karena artifact jadi lebih self-describing.

Kita bisa lihat model expected columns dan type.

Ini bantu serving dan debugging.

---

## Common mistake: log everything

MLflow bisa simpan banyak metadata, tapi bukan berarti semua hal harus dilog.

Kalau log 500 random params yang nggak pernah dipakai buat comparison, UI justru noisy.

Tanya:

> “Apa yang dibutuhkan untuk reproduce, compare, dan trace run?”

Logging yang purposeful lebih valuable daripada logging banyak.

---

## Common mistake: metric tanpa context

MAE 10.2 sendirian belum lengkap.

Kita juga butuh:

~~~text
on what validation period?
using what snapshot?
what model config?
what baseline?
~~~

Context matters.

---

## Hands-on mindset

Saat buka MLflow UI nanti, jangan cuma lihat row paling atas.

Klik run.

Cari:

- parameters,
- metrics,
- tags,
- artifacts,
- run ID,
- dataset metadata.

Coba explain run itu seperti kalian lagi review experiment orang lain.

Kalau bisa, tracking system-nya sudah meaningful.

---

## Checkpoint

1. Experiment beda apa dengan Run?
2. Parameter beda apa dengan Metric?
3. Artifact itu apa?
4. Kenapa baseline ikut dilog?
5. Dataset fingerprint buat apa?
6. Tracking beda apa dengan Registry?

Kalau clear, Model Registry section berikutnya bakal jauh lebih gampang.
