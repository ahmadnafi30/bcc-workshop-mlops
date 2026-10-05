# MLflow Model Registry — Dari Experiment Menjadi Model yang Bisa Dipilih

## Tracking belum menjawab semuanya

MLflow Tracking bisa menunjukkan semua runs.

Tapi application butuh satu keputusan:

> “Model mana yang dipakai?”

Kalau ada 30 runs, API nggak boleh random pilih run dengan MAE kecil.

Kita butuh lifecycle setelah experiment.

Itulah Model Registry.

---

# Registered model

Kita punya logical model name:

~~~text
taxi-demand-forecasting-model
~~~

Di bawahnya ada version:

~~~text
version 1
version 2
version 3
...
~~~

Setiap version linked ke source MLflow run.

---

# Run vs version

## Run

Satu experiment execution.

Bisa baseline, failed idea, candidate, apa saja.

## Model version

Model artifact yang secara explicit diregister.

Jadi:

~~~text
not every run
becomes
model version
~~~

---

# Register

~~~bash
uv run python scripts/register_model.py   --run-id <RUN_ID>
~~~

MLflow create new version.

Project lalu assign alias challenger untuk candidate.

---

# Challenger

~~~text
challenger
→ model candidate
~~~

Meaning:

> “This is the model we are currently considering.”

Belum production.

---

# Champion

~~~text
champion
→ approved serving model
~~~

FastAPI load:

~~~text
models:/taxi-demand-forecasting-model@champion
~~~

Tidak hard-code version.

---

# Kenapa alias bagus?

Bad approach:

~~~text
API config:
MODEL_VERSION=3
~~~

Setiap promotion harus edit app config/code.

Dengan alias:

~~~text
champion → v3
~~~

later:

~~~text
champion → v5
~~~

Application tetap resolve champion.

Model governance separated dari application code.

---

# Promotion

~~~bash
uv run python scripts/promote_model.py   --version 5
~~~

Alias champion pindah.

---

# Training, registration, promotion adalah tiga hal berbeda

~~~text
training
→ produce model artifact

registration
→ create managed model version

promotion
→ decide serving alias
~~~

Kalau tiga concept ini dicampur, lifecycle model jadi susah diaudit.

---

# Kenapa nggak auto-promote setiap retrain?

Karena:

~~~text
new
≠
better
≠
safe for production
~~~

Project kita otomatis bisa menghasilkan challenger.

Tapi champion tetap explicit review.

Ini intentional governance boundary.

---

# Lineage

Suppose API response bilang:

~~~text
model_version = 3
run_id = abc123
~~~

Kita bisa trace:

~~~text
champion
↓
version 3
↓
run abc123
↓
validation MAE
params
dataset SHA
artifact
~~~

Itu model lineage.

---

# Rollback

Kalau new champion ternyata problematic, alias bisa diarahkan ke older version.

Mental model:

~~~text
change pointer
not rewrite app
~~~

Real production mungkin punya approval/audit flow lebih strict, tapi fundamental idea sama.

---

# Monitoring-driven challenger

Later flow:

~~~text
recent MAE degraded
↓
retrain
↓
new MLflow run
↓
beat baseline?
↓
register version
↓
challenger
~~~

Champion masih unchanged.

Reviewer kemudian decide.

---

# Checkpoint

Kalau kalian bisa explain empat term:

~~~text
run
model version
challenger
champion
~~~

Registry concept sudah solid.
