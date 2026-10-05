# Step 10 — Retraining: Dari Signal Monitoring Sampai Challenger Baru

Ini final hands-on lifecycle kita.

Sebelumnya kita sudah melakukan:

~~~text
data
↓
feature engineering
↓
snapshot
↓
training
↓
tracking
↓
registry
↓
serving
↓
monitoring
~~~

Sekarang pertanyaan terakhir:

> “Kalau monitoring bilang champion mulai memburuk, apa yang seharusnya system lakukan?”

Jawabannya bukan langsung:

> “Replace production model sekarang!”

Kita ingin lifecycle yang lebih controlled:

~~~text
detect
↓
decide
↓
retrain if needed
↓
create challenger
↓
review
↓
promote
~~~

Di sini kita benar-benar menutup feedback loop MLOps.

---

## Goal

Setelah step ini kalian harus bisa menjelaskan:

- reference MAE datang dari mana;
- kenapa threshold relative;
- kenapa minimum sample diperlukan;
- kenapa monitoring run bisa success tanpa retrain;
- bagaimana cutoff retraining ditentukan;
- kenapa snapshot baru dibuat;
- kenapa runtime worker tidak auto-commit Git/DVC;
- kenapa validation window ikut maju;
- kenapa baseline tetap jadi guardrail;
- challenger vs champion;
- automatic retraining vs automatic promotion;
- bagaimana serving akhirnya detect champion baru.

Kalau semua ini clear, kalian sudah paham lifecycle decision, bukan cuma command-nya.

---

# 1. Jangan trigger DAG dulu — baca evidence-nya

Open:

~~~text
data/monitoring/performance_summary.json
~~~

Cari:

~~~text
evaluation_count
recent_mae
recent_rmse
reference_mae
threshold_mae
retrain_recommended
latest_target_datetime
model_version
~~~

Kenapa baca manual dulu?

Karena Airflow tidak seharusnya menjadi black box decision maker.

Kita harus tahu input decision sebelum automation act.

---

# 2. Reference MAE datang dari mana?

Monitoring code memanggil champion reference dari MLflow.

Concept:

~~~text
champion alias
↓
model version
↓
source run
↓
validation MAE
~~~

Jadi reference bukan angka random yang ditulis lagi di monitoring script.

Lineage dipakai.

Kalau champion berubah, reference performance juga bisa berubah sesuai source run model baru.

---

# 3. Hitung threshold sendiri

Suppose:

~~~text
reference_mae = 10
degradation_multiplier = 1.25
~~~

Threshold:

~~~text
10 × 1.25 = 12.5
~~~

Sekarang:

~~~text
recent_mae = 13.2
evaluation_count = 250
min_samples = 100
~~~

Decision:

~~~text
13.2 > 12.5
AND
250 >= 100
↓
retrain_recommended = true
~~~

Simple rule.

Tapi dia punya reasoning yang jelas.

---

# 4. Kenapa threshold relative?

Bayangin dua ML task.

Task A:

~~~text
normal MAE sekitar 0.8
~~~

Task B:

~~~text
normal MAE sekitar 120
~~~

Kalau kita pakai universal:

~~~text
retrain if MAE > 20
~~~

Task A telat banget bereaksi.

Task B mungkin selalu retrain.

Relative threshold anchor ke known champion quality.

Masih simplification, tapi lebih portable secara semantics.

---

# 5. Kenapa multiplier 1.25?

Jangan anggap 1.25 angka sakral.

Dia workshop default supaya mudah dijelaskan.

Production policy seharusnya mempertimbangkan:

- business tolerance;
- noise;
- sample volume;
- cost of wrong prediction;
- cost of retraining;
- seasonality;
- segment behavior.

Nilai threshold adalah policy decision, bukan universal law Machine Learning.

---

# 6. Minimum sample

Case:

~~~text
recent_mae = 30
evaluation_count = 3
~~~

Haruskah retrain?

Belum tentu.

Tiga sample sangat mudah dipengaruhi outlier.

Makanya kita punya:

~~~text
min_samples = 100
~~~

Decision butuh:

~~~text
magnitude of degradation
+
enough evidence
~~~

Ini seperti kita nggak mau ganti resep restoran cuma karena satu customer bilang kurang asin.

Kita cari pattern.

---

# 7. recent_limit

Default:

~~~text
recent_limit = 500
~~~

Kenapa tidak pakai semua historical prediction?

Karena monitoring ingin menjawab:

> “Bagaimana behavior terbaru?”

Kalau six months old performance masuk dengan weight besar, recent degradation bisa tertutup average lama.

Recent window memberi sensitivity ke current behavior.

---

# 8. Open Airflow monitoring DAG

Buka:

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

Tapi second task punya conditional lifecycle cukup panjang.

Sebelum trigger, lihat parameter form.

Expected default:

~~~text
degradation_multiplier = 1.25
min_samples = 100
recent_limit = 500
~~~

---

# 9. Predict outcome sebelum Trigger

Lihat performance_summary.

Kalau:

~~~text
retrain_recommended = false
~~~

coba predict:

> “Apa maybe_retrain akan train model?”

Expected:

~~~text
no
~~~

Kalau true, expect:

~~~text
snapshot
↓
training
↓
MLflow run
↓
candidate gate
↓
challenger
~~~

Baru trigger.

Again: hypothesis before clicking.

---

# 10. Task evaluate_model

Actual DAG call:

~~~text
evaluate_champion_performance
~~~

Function ini:

~~~text
resolve champion reference
↓
load prediction log
↓
build evaluation table
↓
summarize performance
↓
save evaluation parquet
↓
save summary JSON
↓
return summary
~~~

Jadi Airflow task tidak duplicate calculation logic.

Reusable logic tetap di src/monitoring dan orchestration module.

---

# 11. Healthy path

Kalau monitoring_result:

~~~text
retrain_recommended = false
~~~

function return:

~~~text
status = not_needed
reason = performance_within_threshold
~~~

DAG success.

Pause di sini.

Ini penting banget:

> **Automation success tidak selalu berarti action executed.**

Kadang decision paling tepat adalah mempertahankan champion.

Kalau system selalu retrain setiap monitoring run, condition check jadi pointless.

---

# 12. No evaluated predictions path

Ada case:

~~~text
latest_target_datetime = null
~~~

Misalnya belum ada prediction yang ground truth-nya available.

Correct behavior:

~~~text
not_needed
reason = no_evaluated_predictions
~~~

Bukan force training.

Unknown evidence bukan signal degradation.

---

# 13. Degraded path — overview

Kalau recommendation true:

~~~text
latest_target_datetime
↓
derive cutoff_date
↓
create retraining snapshot
↓
train candidate
↓
log MLflow stage retraining-validation
↓
compare with naive baseline
↓
register challenger if eligible
~~~

Mari bedah detailnya.

---

# 14. latest_target_datetime menjadi cutoff

Suppose latest evaluated target:

~~~text
2025-02-10 23:00
~~~

Code ambil date:

~~~text
2025-02-10
~~~

Kenapa cutoff berdasarkan evaluated target?

Karena kita tahu ground truth legitimate tersedia sampai logical point itu.

Historical replay harus menjaga temporal integrity.

Kita nggak mau retraining memakai future data yang belum seharusnya available.

---

# 15. Create retraining snapshot

Feature dataset aktif bisa terus berkembang.

Retraining freeze data sampai cutoff.

Output misalnya:

~~~text
data/snapshots/training/taxi_demand_2025-02-10.parquet
~~~

Metadata snapshot:

~~~text
name
rows
zones
sha256
~~~

Kenapa hash lagi?

Supaya MLflow run punya identity data yang kuat.

---

# 16. Initial DVC snapshot vs runtime retraining snapshot

Ini nuance yang bagus buat dibahas.

Initial training:

~~~text
DVC repro
↓
reproducible training snapshot stage
~~~

Runtime retraining:

~~~text
Airflow
↓
create snapshot for latest cutoff
↓
log snapshot fingerprint to MLflow
~~~

Kenapa Airflow tidak otomatis:

~~~text
git add
git commit
dvc commit
git push
~~~

Karena runtime worker jangan diam-diam mutate source repository sebagai side effect training.

Source-control workflow dan runtime artifact workflow punya responsibility beda.

Production matang biasanya save runtime snapshot ke versioned object storage/artifact system.

Workshop kita log frozen file + SHA ke MLflow.

---

# 17. Train candidate dengan same experiment logic

Retraining reuse:

~~~text
run_mlflow_experiment
~~~

Stage tag:

~~~text
retraining-validation
~~~

Kenapa reuse?

Supaya initial training dan retraining tidak pelan-pelan diverge.

Kalau initial flow calculate metric satu cara dan retraining flow punya implementation beda, comparison menjadi susah dipercaya.

One reusable experiment function menjaga consistency.

---

# 18. Moving validation window

Split model sekarang dinamis.

Rule:

> last 5 days of snapshot = validation.

Initial snapshot sampai Jan 26:

~~~text
training
→ earlier model-ready rows through Jan 21

validation
→ Jan 22–26
~~~

Snapshot retraining sampai Feb 10:

~~~text
training
→ through Feb 5

validation
→ Feb 6–10
~~~

Kenapa validation ikut maju?

Karena kita ingin evaluate candidate pada recent unseen period.

Kalau February model masih diuji hanya January holdout, kita belum menjawab apakah dia generalize ke recent behavior.

---

# 19. Kenapa validation tidak pakai random split?

Sama seperti initial training.

Time-series problem punya temporal order.

Random split bisa membuat future-like rows masuk training sementara older rows masuk validation.

Kita ingin simulation:

~~~text
learn from past
↓
validate on later period
~~~

Retraining tidak mengubah prinsip temporal validation.

---

# 20. Baseline gate

Setelah candidate train, experiment result punya:

~~~text
model_beats_baseline
~~~

register_challenger check ini.

Kalau false:

~~~text
status = not_registered
reason = model_did_not_beat_baseline
~~~

Kenapa baseline masih dibutuhkan?

Karena data baru bisa membuat complex model perform buruk.

Tidak ada guarantee gradient boosting selalu menang selamanya.

Baseline adalah guardrail setiap cycle.

---

# 21. Apakah beat baseline cukup buat jadi champion?

No.

Ini distinction penting.

~~~text
beat naive baseline
→ candidate layak dipertimbangkan

beat current champion under all relevant criteria
→ belum tentu
~~~

Misalnya candidate:

~~~text
MAE sedikit lebih baik
latency jauh lebih buruk
~~~

atau:

~~~text
overall MAE bagus
zone penting tertentu jelek
~~~

Workshop belum punya semua governance check itu.

Makanya automatic step berhenti di challenger.

---

# 22. Challenger alias

Kalau candidate eligible:

~~~text
register model version
↓
set alias challenger
~~~

Sekarang Registry punya candidate baru yang traceable ke:

~~~text
run ID
snapshot
metrics
params
~~~

Review bisa dilakukan dengan evidence.

---

# 23. Review sebelum promotion

Minimal inspect:

~~~text
candidate validation MAE
candidate RMSE
baseline MAE
dataset cutoff
dataset SHA
source run
current champion reference
recent champion production-like MAE
~~~

Kalau cuma lihat version baru lebih besar nomornya, itu bukan model review.

Version number tidak imply quality.

---

# 24. Promote explicit

Kalau approved:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

Registry:

~~~text
champion
↓
new version
~~~

Kita tidak edit API source code.

---

# 25. Bagaimana API detect champion baru?

RegistryModelLoader periodically refresh metadata.

Suppose current cache:

~~~text
v3
~~~

Promotion:

~~~text
champion → v5
~~~

After refresh interval:

~~~text
query champion
↓
version changed?
↓ yes
load v5
↓
cache v5
~~~

Future requests use v5.

Ini close loop Registry → Serving.

---

# 26. Policy sensitivity experiment

Di local workshop, kita boleh experiment parameter.

Example:

~~~text
multiplier = 1.25
vs
multiplier = 1.05
~~~

1.05 lebih sensitive.

Apakah otomatis lebih bagus?

No.

Terlalu sensitive:

~~~text
small noise
↓
retrain often
↓
compute waste
↓
many challengers
↓
review fatigue
~~~

Terlalu loose:

~~~text
model degraded
↓
system wait too long
↓
bad predictions persist
~~~

Threshold adalah control policy tradeoff.

---

# 27. Thermostat analogy

Bayangin thermostat rumah.

Kalau threshold terlalu sensitive:

~~~text
temperature berubah 0.1°
↓
AC on
↓
off
↓
on
↓
off
~~~

System oscillate.

Monitoring policy juga bisa begitu:

~~~text
tiny MAE fluctuation
↓
retrain
↓
tiny fluctuation
↓
retrain lagi
~~~

Kita ingin stable decision, bukan hyperactive automation.

---

# 28. Retraining tidak solve bad data

Suppose MAE naik karena processed data corruption.

Kalau response kita:

~~~text
bad data
↓
retrain
↓
model learns bad data
~~~

kita memperburuk problem.

Mature lifecycle biasanya punya data-quality gate juga.

Jadi retrain recommendation berarti condition for candidate refresh reached, bukan root cause pasti model lama.

---

# 29. Batch retraining vs continual learning

Project kita:

~~~text
batch retraining
~~~

Flow:

~~~text
collect newer data
↓
freeze snapshot
↓
train new model
↓
replace only after review
~~~

Continual/online learning:

~~~text
new observations
↓
incrementally update model parameters
~~~

Dua paradigm beda.

Pipeline kita berulang bukan berarti continual learning.

---

# 30. Full lifecycle tanpa nama tools

Sekarang coba cerita full project tanpa sebut tool.

Contoh:

> “Kita menerima data historical secara bertahap, aggregate jadi demand per zone-hour, membangun feature hanya dari masa lalu, membekukan training input, mencatat experiment, memilih model approved, expose prediction lewat service, menyimpan prediction, menunggu actual, menghitung recent error, dan kalau performance cukup memburuk dengan evidence yang cukup, kita train candidate baru lalu review sebelum production replacement.”

Kalau narrative ini sudah bisa dijelaskan, baru mapping tool:

~~~text
data orchestration
→ Airflow

snapshot
→ DVC

experiment + registry
→ MLflow

serving
→ FastAPI

runtime
→ Docker

code lifecycle
→ GitHub Actions

metrics
→ Prometheus

dashboard
→ Grafana
~~~

Ini lebih powerful daripada hafal list tools dulu.

---

# Final challenge

### Scenario 1

Recent MAE naik, sample cuma 8.

Action?

~~~text
wait / insufficient evidence
~~~

### Scenario 2

Recent MAE naik, sample 500, threshold exceeded.

Action?

~~~text
create retraining candidate
~~~

### Scenario 3

Candidate beat baseline.

Auto champion?

~~~text
no
review first
~~~

### Scenario 4

Candidate promoted to champion.

Edit FastAPI version constant?

~~~text
no
serving resolves alias
~~~

### Scenario 5

MAE naik karena data corrupt.

Retrain directly?

~~~text
investigate/fix data first
~~~

Kalau reasoning ini clear, feedback loop-nya benar-benar dipahami.

---

# Final checkpoint

1. Reference MAE datang dari mana?
2. Kenapa multiplier bukan universal truth?
3. Minimum samples solve apa?
4. recent_limit buat apa?
5. Healthy monitoring run boleh no-op kenapa?
6. latest_target_datetime dipakai buat apa?
7. Kenapa retraining snapshot baru diperlukan?
8. Kenapa runtime Airflow tidak auto Git commit?
9. Kenapa validation window bergerak?
10. Kenapa time split tetap chronological?
11. Baseline gate solve apa?
12. Beat baseline kenapa belum otomatis champion?
13. Challenger dan champion beda apa?
14. Threshold terlalu sensitive efeknya apa?
15. Threshold terlalu loose efeknya apa?
16. Kenapa retraining tidak solve corrupt data?
17. Batch retraining vs continual learning?
18. Bagaimana API detect champion baru?

Kalau kalian bisa jawab dengan bahasa sendiri, congratulations peers — kalian sudah bukan cuma mengikuti command MLOps. Kalian sudah mulai memahami **kenapa lifecycle-nya dirancang seperti ini**.
