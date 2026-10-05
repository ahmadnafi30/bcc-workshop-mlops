# Step 10 — Retraining: Closing the Loop

Kita sudah sampai final loop.

Model sudah:

- trained,
- registered,
- served,
- monitored.

Sekarang pertanyaan terakhir:

> “Kalau performa memburuk, system ngapain?”

---

# 1. Inspect current summary

Open:

~~~text
data/monitoring/performance_summary.json
~~~

Look at:

~~~text
recent_mae
reference_mae
threshold_mae
evaluation_count
retrain_recommended
~~~

---

# 2. Understand decision before triggering DAG

Default:

~~~text
threshold
=
reference MAE × 1.25
~~~

dan:

~~~text
minimum evaluation samples
=
100
~~~

Jadi condition:

~~~text
recent_mae > threshold_mae
AND
evaluation_count >= min_samples
~~~

---

# 3. Healthy model is a valid outcome

Kalau:

~~~text
retrain_recommended = false
~~~

jangan kecewa karena “demo retrain nggak jalan”.

Justru itu correct decision.

Automation shouldn’t create unnecessary work.

---

# 4. Open Airflow monitoring DAG

~~~text
taxi_model_monitoring
~~~

Graph:

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Trigger.

---

# 5. Evaluate task

Task akan:

1. resolve champion from MLflow;
2. get champion validation MAE;
3. load prediction logs;
4. join available actual demand;
5. calculate recent metric;
6. save summary.

---

# 6. maybe_retrain

Kalau healthy:

~~~text
status = not_needed
~~~

Kalau degraded:

~~~text
latest evaluated date
↓
new training snapshot
↓
MLflow training
↓
latest 5-day validation
↓
candidate metric
↓
beat naive baseline?
↓
register challenger
~~~

---

# 7. Why latest five days?

Retraining snapshot baru lebih panjang.

Validation harus move.

Misalnya snapshot sampai Feb 10.

~~~text
train:
older history through Feb 5

validation:
Feb 6–10
~~~

Kalau validation tetap Jan 22–26 selamanya, kita nggak test recent behavior.

---

# 8. Inspect new MLflow run

Kalau retrain terjadi, buka MLflow.

Cari run dengan stage:

~~~text
retraining-validation
~~~

Compare dengan initial run.

Look at:

- dataset snapshot name,
- dataset SHA,
- MAE,
- RMSE,
- row count.

---

# 9. Inspect Registry

Candidate baru bisa jadi:

~~~text
challenger
~~~

Champion belum berubah.

---

# 10. Why no auto champion?

Misalnya new model:

~~~text
beats naive baseline
~~~

tapi:

~~~text
still worse than current champion
~~~

Kalau auto-promote berdasarkan baseline saja, production could regress.

Makanya promotion explicit.

---

# 11. Review before promotion

Checklist:

- candidate MAE?
- candidate RMSE?
- current champion validation?
- production-like recent MAE?
- newer snapshot?
- run metadata valid?

Kalau approved:

~~~bash
uv run python scripts/promote_model.py   --version <VERSION>
~~~

---

# 12. Serving picks it up

FastAPI loader periodically refresh Registry metadata.

Setelah alias champion pindah:

~~~text
old version
→
new version
~~~

next refresh/load akan use new champion.

No API source edit.

---

# Full loop

Sekarang complete:

~~~text
data
↓
features
↓
snapshot
↓
train
↓
track
↓
register
↓
champion
↓
serve
↓
log
↓
ground truth
↓
monitor
↓
retrain
↓
challenger
↓
review
↓
champion
~~~

Inilah end-to-end MLOps story workshop kita.

---

# Final reflection

Coba jawab tiga pertanyaan:

### 1

Kenapa retraining otomatis tapi promotion manual?

### 2

Kenapa recent MAE compare ke champion validation MAE?

### 3

Kenapa application load alias champion bukan version number?

Kalau kalian bisa jawab dengan bahasa sendiri, lifecycle sudah benar-benar masuk.
