# Step 4 — MLflow: Tracking Runs and Registering a Champion

Sekarang kita sudah punya reproducible snapshot.

Masalah selanjutnya:

> “Kalau saya train berkali-kali, gimana cara tracking result-nya tanpa spreadsheet manual?”

MLflow masuk di sini.

---

# Part A — Start Tracking Server

~~~bash
uv run python scripts/start_mlflow.py
~~~

Keep terminal ini running.

Open:

~~~text
http://127.0.0.1:5000
~~~

Kalau UI terbuka, server ready.

---

# Kenapa helper, bukan mlflow server plain?

Helper memastikan local state disimpan ke:

~~~text
.mlflow/
~~~

Nanti Compose MLflow juga pakai folder sama.

Jadi model/registry tidak hilang saat pindah stage.

---

# Part B — Run tracked training

Open terminal baru.

~~~bash
uv run python scripts/train_with_mlflow.py
~~~

Script log baseline + HGB run.

---

# 1. Open MLflow UI

Cari experiment taxi demand forecasting.

Kalian harus lihat multiple runs.

Jangan cuma lihat MAE.

Open model run.

---

# 2. Inspect parameters

Cari:

~~~text
learning_rate
max_iter
dataset_snapshot
train_rows
validation_rows
~~~

Pertanyaan:

> Kalau saya rerun model dengan learning_rate berbeda, di mana bedanya terlihat?

Di Parameters.

---

# 3. Inspect metrics

~~~text
mae
rmse
~~~

Bandingkan baseline.

---

# 4. Inspect tags

Cari stage/model family.

Tags membantu context.

---

# 5. Inspect artifacts

Lihat model artifact.

Ini linked ke run.

---

# 6. Copy model run ID

Terminal atau UI punya run ID.

Misalnya:

~~~text
abc123...
~~~

Kita akan register model dari source run ini.

---

# Part C — Register candidate

~~~bash
uv run python scripts/register_model.py   --run-id <RUN_ID>
~~~

Open Model Registry.

Cari:

~~~text
taxi-demand-forecasting-model
~~~

Harus ada model version.

Alias:

~~~text
challenger
~~~

---

# 7. Why challenger?

Kita sengaja belum champion.

New model = candidate.

Butuh approval.

---

# Part D — Promote champion

Setelah review:

~~~bash
uv run python scripts/promote_model.py   --version <VERSION>
~~~

Sekarang Registry alias:

~~~text
champion
~~~

point ke selected version.

---

# 8. Trace lineage

Klik champion version.

Cari source run.

Dari run, lihat:

- metric,
- params,
- dataset SHA.

Chain:

~~~text
champion
↓
version
↓
run
↓
dataset snapshot + metric
~~~

Kalau kalian bisa navigate chain ini, model lineage concept sudah kebayang.

---

# Mini challenge

Kenapa API nanti load:

~~~text
@champion
~~~

bukan version number?

Karena model selection bisa berubah tanpa harus edit serving code.

---

# Common issue

## MLflow UI kosong

Pastikan training code connect ke same tracking URI.

## Register fails

Pastikan run ID valid dan model artifact exists.

## Champion missing

Promotion script belum dijalankan.

---

# Checkpoint

Sebelum Airflow, pastikan:

- MLflow UI accessible,
- tracked model run exists,
- Registry punya challenger,
- selected version punya champion alias.

Next kita orchestrate workflow.
