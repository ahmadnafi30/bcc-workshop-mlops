# Retraining — When Should We Create a New Model?

## Retraining jangan jadi ritual

Sering ada pattern:

> “Model ML harus retrain tiap malam.”

Kenapa?

> “Ya karena production.”

Belum tentu.

Retraining punya cost:

- compute,
- evaluation,
- new artifact,
- review,
- possible regression.

Kita sebaiknya punya reason.

---

# Trigger kita: performance degradation

Kita compare:

~~~text
recent MAE
vs
champion validation MAE
~~~

Default threshold:

~~~text
recent_mae
>
reference_mae × 1.25
~~~

dan:

~~~text
evaluation_count >= 100
~~~

---

# Contoh

Champion validation:

~~~text
MAE = 10
~~~

Multiplier:

~~~text
1.25
~~~

Threshold:

~~~text
12.5
~~~

Recent MAE:

~~~text
11.4
~~~

No retrain.

Kalau:

~~~text
recent MAE = 14.0
sample = 300
~~~

recommend retrain.

---

# Kenapa minimum sample?

Satu hour bisa extreme.

Event khusus.

Weather weird.

Data issue.

Kalau satu bad point langsung trigger training, system terlalu reactive.

Minimum sample memberi evidence lebih stable.

---

# Why recent window?

Suppose historical MAE selama enam bulan bagus.

Minggu terakhir rusak.

Kalau calculate all-time average, recent degradation bisa diluted.

Kita care current performance.

Jadi recent window more actionable.

---

# Airflow monitoring DAG

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

evaluate_model:

1. load champion reference from MLflow;
2. load prediction logs;
3. join available ground truth;
4. calculate recent metrics;
5. save performance summary.

maybe_retrain inspect summary.

---

# Healthy path

~~~text
retrain_recommended = false
↓
status = not_needed
~~~

Ini bukan failure.

Ini correct automation outcome.

Automation tidak harus selalu melakukan sesuatu.

---

# Degraded path

~~~text
retrain recommended
↓
latest evaluated cutoff
↓
new snapshot
↓
train
↓
latest 5 days validation
↓
MLflow run
↓
beat naive baseline?
↓
register challenger
~~~

---

# Moving validation window

Initial:

~~~text
Jan 8–21 train
Jan 22–26 validation
~~~

Later snapshot sampai Feb 10:

~~~text
older rows through Feb 5
train

Feb 6–10
validation
~~~

Validation moves with data.

Kenapa?

Karena kita ingin test model on latest unseen-ish period.

Kalau validation tetap Jan forever, retraining evaluation nggak represent current temporal behavior.

---

# Auto retrain vs auto promote

Ini boundary penting.

~~~text
automatic:
monitor
retrain
register challenger

manual:
promote challenger to champion
~~~

Kenapa manual?

Karena model baru mungkin:

- beat naive baseline,
- tapi masih worse than champion,
- punya weird segment behavior,
- butuh human/business review.

Jadi production promotion lebih sensitive.

---

# Continual learning beda

Project kita batch retraining.

~~~text
collect newer dataset
↓
train new model
~~~

Ini bukan continual/online learning yang update model weights incrementally setiap stream data datang.

Terminology penting.

---

# What if ground truth unavailable?

No evaluation.

No evidence.

No retraining decision.

System harus tolerate delayed/missing ground truth.

Workshop skip predictions yang actual belum available.

---

# What if recent MAE good?

Do nothing.

Ini actually healthy.

Jangan force retraining hanya supaya demo terlihat “aktif”.

Presenter bisa explain both branch.

---

# Final lifecycle

~~~text
Champion serves
↓
Predictions logged
↓
Ground truth arrives
↓
Performance evaluated
↓
Degraded?
├── no → keep champion
└── yes
     ↓
   retrain
     ↓
   challenger
     ↓
   review
     ↓
   promote
     ↓
   new champion
~~~

Ini feedback loop yang kita bangun dari awal workshop.

Dan ini point di mana semua tool akhirnya nyambung.
