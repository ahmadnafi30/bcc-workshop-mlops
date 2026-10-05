# Step 10 — Retraining: Menutup Feedback Loop

Ini final lifecycle step.

Kita sudah:

~~~text
train
track
register
serve
monitor
~~~

Sekarang kalau evidence bilang model degraded, apa yang terjadi?

---

## Goal

Setelah step ini:

- performance summary dipahami,
- monitoring DAG dijalankan,
- healthy path dipahami,
- degraded path dipahami,
- challenger lifecycle dipahami,
- promotion tetap explicit.

---

## 1. Buka summary

~~~text
data/monitoring/performance_summary.json
~~~

Cari:

~~~text
recent_mae
reference_mae
threshold_mae
evaluation_count
retrain_recommended
~~~

Before Airflow, kalian harus ngerti decision input.

Automation bukan alasan buat hide logic.

---

## 2. Hitung manual

Misalnya:

~~~text
reference = 10
multiplier = 1.25
~~~

Threshold:

~~~text
12.5
~~~

Kalau recent = 13 dan samples 200:

~~~text
retrain recommended
~~~

Kalau samples 5:

~~~text
not enough evidence
~~~

---

## 3. Open monitoring DAG

Airflow:

~~~text
taxi_model_monitoring
~~~

Graph:

~~~text
evaluate_model
↓
maybe_retrain
~~~

Kelihatannya cuma dua task.

Tapi maybe_retrain encapsulate conditional lifecycle.

---

## 4. Trigger default params

~~~text
degradation_multiplier = 1.25
min_samples = 100
recent_limit = 500
~~~

Run.

---

## 5. Healthy path

Kalau model healthy:

~~~text
status = not_needed
~~~

Jangan kecewa. 😭

Ini actually good.

Pipeline observe dan decide no action.

Automation yang selalu retrain justru suspicious.

---

## 6. Degraded path

Kalau condition met:

~~~text
latest evaluated date
↓
snapshot
↓
train
↓
validation
↓
MLflow
↓
baseline gate
↓
challenger
~~~

---

## 7. Inspect MLflow

Cari run stage:

~~~text
retraining-validation
~~~

Compare:

- dataset snapshot,
- SHA,
- MAE,
- RMSE,
- date range.

Question:

> “Apakah snapshot sama dengan initial?”

Harusnya lebih baru.

---

## 8. Validation moves

Initial validation January.

Retrain snapshot later → last 5 days move.

Kenapa?

Kita mau evaluate on recent holdout, bukan old frozen January forever.

---

## 9. Registry

Kalau candidate pass baseline gate, challenger alias update.

Champion belum berubah.

This is intentional.

---

## 10. Manual review

Before promotion, inspect:

~~~text
candidate MAE
current champion
recent production-like error
dataset period
run lineage
~~~

Lalu kalau approved:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

---

## 11. Serving picks new champion

API loader periodically check alias.

Setelah champion move, future prediction bisa use new model.

No source code hard-code version.

Closed loop:

~~~text
serve
↓
monitor
↓
evaluate
↓
retrain
↓
challenger
↓
review
↓
champion
↓
serve
~~~

---

## Final challenge

Coba jelaskan full lifecycle tanpa lihat diagram.

Mulai dari:

> “NYC TLC monthly data...”

dan finish:

> “...new champion diserve.”

Kalau bisa explain causality-nya, bukan cuma nama tools, berarti workshop goal tercapai.
