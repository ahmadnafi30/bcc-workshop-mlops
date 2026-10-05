# Retraining — Kapan Model Perlu Belajar Lagi?

“Auto retrain tiap hari” kedengarannya keren.

Tapi automation yang keren belum tentu automation yang benar.

Retraining punya cost:

- compute;
- time;
- experiment noise;
- model review;
- regression risk;
- storage;
- operational complexity.

Jadi pertanyaan yang lebih mature bukan:

> “Seberapa sering kita bisa retrain?”

Tapi:

> **“Evidence apa yang menunjukkan current model perlu candidate baru?”**

Workshop kita pakai performance degradation sebagai trigger.

---

# Default decision rule

~~~text
recent MAE
>
champion validation MAE × 1.25
~~~

dan:

~~~text
evaluated predictions >= 100
~~~

Dua condition harus terpenuhi.

---

# Example

Champion saat validation:

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

Recent production-like MAE:

~~~text
13.4
~~~

Sample count:

~~~text
350
~~~

Result:

~~~text
13.4 > 12.5
and
350 >= 100
↓
retrain recommended
~~~

---

# Kenapa bukan fixed MAE 20?

Karena metric scale tergantung problem.

Task A mungkin normal MAE 1.

Task B mungkin normal MAE 100.

Relative threshold anchor ke expected champion performance.

Ini belum perfect, tapi jauh lebih reasonable daripada random hard-coded universal number.

---

# Kenapa minimum samples?

Case:

~~~text
sample 1
error besar banget
~~~

Haruskah retrain?

Belum tentu.

Bisa one-off anomaly.

Kalau automation langsung react ke satu data point, kita punya high-variance control system.

Minimum samples menambah evidence requirement.

---

# Apa yang terjadi kalau ground truth belum cukup?

Correct action:

~~~text
wait
~~~

Bukan:

~~~text
force retrain
~~~

Automation bisa menghasilkan:

~~~text
not_needed
not_enough_evidence
~~~

Itu valid.

Sistem tidak harus melakukan action setiap kali workflow jalan.

---

# Monitoring DAG

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Task evaluate menghitung summary.

Task maybe_retrain baca recommendation.

Healthy:

~~~text
performance within threshold
↓
return not_needed
↓
DAG success
~~~

Degraded:

~~~text
retrain recommended
↓
create new snapshot
↓
train
↓
validate
↓
log MLflow
↓
candidate check
↓
register challenger
~~~

---

# Kenapa new snapshot?

Kalau retraining read moving latest feature file tanpa freeze:

> “Model ini sebenarnya train dari data exact yang mana?”

jadi susah dijawab.

Snapshot memberi:

- cutoff date;
- row count;
- data hash;
- stable training input.

Lineage tetap kuat.

---

# Cutoff date dari latest evaluated target

Monitoring tahu ground truth available sampai kapan.

Itu membantu menentukan data yang safe dipakai untuk retraining.

Kita tidak ingin include future data yang belum seharusnya available pada logical time.

Historical replay harus tetap preserve temporal dependency.

---

# Validation window ikut maju

Initial training:

~~~text
older history
→ train

latest 5 days
→ validation
~~~

Retraining di February:

~~~text
older history sampai Feb 5
→ train

Feb 6–10
→ validation
~~~

Kenapa validation nggak fixed Jan 22–26 selamanya?

Karena kita ingin tahu:

> “Model baru generalize ke recent period nggak?”

Kalau validation selalu old period, retraining evaluation kurang relevant ke current behavior.

---

# Baseline tetap ada saat retraining

Setiap new candidate harus tetap dibandingkan dengan naive baseline.

Kenapa?

Karena data baru bisa membuat model kompleks malah kalah dari simple daily seasonality.

Rule:

> Complex model tetap harus justify complexity setiap training cycle.

Baseline bukan cuma onboarding artifact.

Dia guardrail.

---

# Candidate vs current champion

Ada nuance.

Project automation register challenger kalau candidate lolos internal criteria tertentu.

Tapi itu belum berarti:

~~~text
candidate automatically superior to champion in all dimensions
~~~

Kita masih bisa compare:

- candidate validation MAE;
- candidate RMSE;
- recent champion performance;
- dataset period;
- business behavior;
- anomaly;
- inference characteristics.

Makanya promotion tetap explicit.

---

# Automatic retraining ≠ automatic promotion

Ini salah satu governance concept paling penting.

Workshop allow:

~~~text
monitoring
↓
automatic retraining
↓
automatic challenger
~~~

Tapi stop sebelum:

~~~text
challenger
↓
champion
~~~

Kenapa?

Karena action impact beda.

Retraining hanya membuat candidate baru.

Promotion mengubah model yang melayani request.

Risk-nya lebih tinggi.

---

# Manual approval bukan berarti MLOps-nya gagal

Ada misconception:

> “Kalau masih ada manual approval berarti belum automation.”

No.

Automation maturity bukan soal manusia harus hilang 100%.

Human-in-the-loop bisa intentional.

Especially kalau:

- financial impact;
- safety;
- regulation;
- business risk;
- model governance.

Goal-nya reliable lifecycle, bukan automation demi automation.

---

# Retraining vs continual learning

Project kita:

~~~text
batch retraining
~~~

Artinya:

~~~text
collect newer dataset
↓
freeze snapshot
↓
train new model from batch
~~~

Continual/online learning:

~~~text
model parameters updated incrementally
as data arrives
~~~

Dua paradigm beda.

Jangan interchangeable.

---

# Setelah promotion

Suppose challenger version 5 approved.

Alias:

~~~text
champion
→ v5
~~~

Serving loader secara periodik refresh Registry metadata.

Setelah detect change:

~~~text
cached v3
↓
alias now v5
↓
load v5
↓
future prediction uses v5
~~~

Application code tetap.

Ini close loop antara Registry dan Serving.

---

# Full Closed Loop

Sekarang lifecycle kita:

~~~text
serve
↓
log prediction
↓
actual arrives
↓
evaluate
↓
degraded?
├── no  → keep champion
└── yes → retrain
          ↓
       challenger
          ↓
         review
          ↓
        promote
          ↓
      serve again
~~~

Nah, ini salah satu bentuk paling tangible dari MLOps feedback loop.

---

# Kapan rule ini belum cukup?

Production system bisa butuh lebih dari:

~~~text
recent MAE > 1.25 × validation MAE
~~~

Possible extensions:

- metric per zone;
- business-weighted error;
- time-of-day segmentation;
- statistical significance;
- data quality gate;
- drift detection;
- minimum improvement over champion;
- inference cost;
- fairness or safety checks.

Workshop memakai simple rule supaya reasoning-nya bisa dilihat jelas.

---

# Failure mode: retraining loop terlalu sensitif

Bayangin threshold terlalu kecil:

~~~text
1.02 × reference MAE
~~~

Sedikit noise bisa trigger retraining terus.

Hasilnya:

- compute waste;
- banyak challenger;
- review fatigue;
- unstable lifecycle.

Ini mirip thermostat yang terlalu sensitif dan nyala-mati terus.

Threshold adalah control-policy decision, bukan sekadar angka teknis.

---

# Failure mode: retraining loop terlalu lambat

Sebaliknya, threshold terlalu longgar:

~~~text
2.0 × reference MAE
~~~

Model mungkin sudah jelek lama sebelum system bereaksi.

Tradeoff:

~~~text
sensitivity
vs
stability
~~~

Real production perlu tune policy berdasarkan business cost.

---

# Retraining bukan obat semua masalah

Kalau MAE naik karena input pipeline corrupt, retraining pada corrupt data malah memperburuk.

Sebelum retrain, mature system biasanya juga check:

- data freshness;
- schema;
- missing values;
- target availability;
- feature sanity.

Jadi retrain recommendation itu signal, bukan excuse untuk skip diagnosis.

---

# Checkpoint

1. Kenapa retrain tiap hari belum tentu bagus?
2. Kenapa threshold relative?
3. Minimum sample solve problem apa?
4. Kenapa retraining pakai snapshot baru?
5. Kenapa validation window ikut maju?
6. Kenapa baseline tetap dibandingkan?
7. Automatic retraining beda apa dengan automatic promotion?
8. Human approval bisa tetap termasuk MLOps kenapa?
9. Batch retraining beda apa dengan continual learning?
10. Setelah champion berubah, serving tahu dari mana?
11. Kenapa threshold terlalu sensitif juga bahaya?
12. Kenapa retraining tidak otomatis solve bad data?

Kalau semua kebayang, feedback loop project kita sudah lengkap dari prediction sampai new model candidate.
