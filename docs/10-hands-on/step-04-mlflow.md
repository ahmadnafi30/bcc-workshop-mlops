# Step 4 — MLflow: Dari “Run Kemarin Kayaknya Bagus” Jadi Experiment yang Bisa Ditelusuri

Sekarang kita punya snapshot yang jelas.

Kalau train sekali, manual metrics masih manageable.

Tapi mulai run kedua, ketiga, keempat, pertanyaan cepat menumpuk:

> “Yang learning_rate 0.05 run mana?”

> “Run paling bagus pakai snapshot hash apa?”

> “Artifact model-nya yang mana?”

> “Baseline run ikut tercatat nggak?”

Di sinilah MLflow Tracking masuk.

Step ini kita akan **buat experiment, inspect lineage, register candidate, lalu promote champion**.

---

## Goal

Setelah selesai kalian harus bisa menjelaskan:

- Tracking URI;
- Experiment vs Run;
- Parameter vs Metric vs Tag vs Artifact;
- baseline run vs model run;
- dataset fingerprint;
- source run → model version lineage;
- challenger vs champion;
- kenapa promotion explicit;
- kenapa local MLflow state dibagi dengan Docker flow.

---

# 1. Start shared MLflow server

Run:

~~~bash
uv run python scripts/start_mlflow.py
~~~

Terminal print:

~~~text
mlflow state: ...
mlflow ui: http://127.0.0.1:5000
~~~

Open browser:

~~~text
http://127.0.0.1:5000
~~~

---

# 2. Kenapa pakai scripts/start_mlflow.py, bukan asal mlflow server?

Helper ini sengaja set:

~~~text
backend store
artifact directory
host/port
allowed hosts
~~~

dan menyimpan state di:

~~~text
.mlflow/
~~~

Folder ini nanti di-mount oleh Docker Compose MLflow.

Jadi flow:

~~~text
local experiment
↓
register champion
↓
stop local MLflow
↓
docker compose up
↓
same Registry state
~~~

Tanpa shared state, participant akan bingung karena model seolah hilang saat pindah mode.

---

# 3. Tracking URI

Training code perlu tahu MLflow server.

Local:

~~~text
http://127.0.0.1:5000
~~~

Container:

~~~text
http://mlflow:5000
~~~

Ini same logical service, beda network perspective.

Tracking URI adalah configuration, bukan model logic.

---

# 4. Sebelum train, buka MLflow UI

Lihat kondisi kosong atau experiment lama.

Kalau fresh state, belum ada run.

Bagus.

Kita akan lihat perubahan setelah command.

Sebelum run, predict:

> “Berapa run yang akan dibuat?”

Training experiment kita log:

~~~text
naive baseline
+
main model
~~~

Jadi expect minimal dua run.

---

# 5. Run tracked training

~~~bash
uv run python scripts/train_with_mlflow.py
~~~

Actual script reuse:

~~~text
run_mlflow_experiment
~~~

Stage:

~~~text
initial-validation
~~~

Terminal output mencakup:

~~~text
tracking uri
experiment name
snapshot
dataset SHA256
baseline MAE + run ID
model MAE + run ID
model URI
~~~

Jangan langsung copy model run ID saja.

Read semua relation-nya.

---

# 6. Experiment vs Run

MLflow Experiment = logical grouping.

Di dalamnya ada Runs.

Analogi:

~~~text
Experiment
→ folder project penelitian

Run
→ satu percobaan
~~~

Project taxi demand punya experiment logical yang sama, tapi banyak runs dari baseline, candidate, retraining.

---

# 7. Buka baseline run

Cari run naive-24h.

Inspect:

### Params

Model type / dataset context.

### Metrics

MAE, RMSE.

### Tags

Task/stage.

Kenapa baseline ikut MLflow?

Karena comparison evidence juga harus traceable.

Kalau baseline cuma print terminal lalu hilang, future reviewer kehilangan context.

---

# 8. Buka main model run

Cari hist-gradient-boosting.

Inspect:

~~~text
Parameters
Metrics
Tags
Artifacts
~~~

Pertanyaan:

> “Apa yang membedakan parameter dan metric?”

Parameter adalah input/config.

Metric adalah measured output.

Example:

~~~text
learning_rate
→ parameter

mae
→ metric
~~~

---

# 9. Dataset metadata

Cari fields seperti:

~~~text
dataset_snapshot
dataset_sha256
dataset_rows
dataset_zones
~~~

Sekarang connect ke Step 3.

DVC memberi snapshot/fingerprint.

MLflow run menyimpan reference context itu.

Jadi kita bisa bilang:

> “Run ini memakai exact snapshot fingerprint ini.”

Ini lineage nyata.

---

# 10. Artifact

Model run punya model artifact.

Kenapa bukan cuma joblib arbitrary file?

MLflow model packaging bisa menyertakan:

- model artifact;
- flavor metadata;
- signature;
- input example.

Artifact linked ke run.

Jadi model file nggak orphan.

---

# 11. Input example dan signature

Inspect model metadata kalau tersedia.

Signature menjelaskan expected input/output schema.

Kenapa useful?

Serving nanti perlu compatible input.

Signature bukan guarantee semua semantics benar, tapi membantu contract visibility.

---

# 12. Compare runs

Pakai MLflow compare UI.

Bandingkan baseline dan model.

Questions:

- model MAE lebih rendah?
- RMSE bagaimana?
- dataset context sama?
- stage sama?

Comparison UI baru meaningful kalau logging metadata konsisten.

---

# 13. Jangan otomatis percaya run terbaru

Newest run bukan necessarily best run.

Version number/time bukan quality.

Kita harus compare metrics/context.

Ini pattern yang nanti sama di Model Registry.

---

# 14. Copy model run ID

Terminal atau UI punya model run ID.

Run:

~~~bash
uv run python scripts/register_model.py --run-id <RUN_ID>
~~~

Default alias:

~~~text
challenger
~~~

Output:

~~~text
name
version
alias
uri
~~~

Sekarang Tracking run berubah status?

Bukan.

Run tetap run.

Registry membuat **model version reference** ke run artifact.

---

# 15. Tracking vs Registry secara visual

~~~text
MLflow Tracking
└── Run abc123
    ├── params
    ├── metrics
    └── model artifact
          ↓ register
MLflow Model Registry
└── taxi-demand-forecasting-model
    └── Version 1
        └── source run abc123
~~~

Ini relation penting banget.

---

# 16. Kenapa alias awal challenger?

Karena new registered model belum automatically production-approved.

New != good.

Registered != champion.

Alias challenger berarti:

> “Candidate ini layak direview.”

---

# 17. Inspect Model Registry

Open registered model.

Lihat:

- model name;
- version;
- source run;
- alias;
- artifact link.

Try click source run.

Kalian harus bisa traverse:

~~~text
model version
↓
experiment run
↓
metrics
↓
dataset SHA
~~~

Kalau bisa, lineage berhasil.

---

# 18. Promotion

Setelah review, run:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

Default target alias:

~~~text
champion
~~~

Now Registry:

~~~text
champion
→ selected version
~~~

---

# 19. Kenapa promotion bukan rename file?

Tanpa registry, mungkin flow:

~~~text
model_v1.joblib
model_v2.joblib
model_final.joblib
model_production.joblib
~~~

Mana actual production?

Ambiguous.

Alias memberi semantic pointer yang explicit dan queryable.

---

# 20. Champion dan challenger bisa point ke version yang sama?

Pada initial setup, bisa saja newly registered version punya challenger lalu juga dipromote champion.

Alias roles tetap beda secara semantics.

Later:

~~~text
champion → v1
challenger → v2
~~~

lebih typical.

---

# 21. Rollback thought experiment

Suppose:

~~~text
champion → v3
~~~

Setelah deployment-like evaluation ternyata v3 buruk.

Old v2 masih registered.

Rollback concept:

~~~text
champion
v3 → v2
~~~

FastAPI tetap query alias champion.

Source code tidak perlu edit.

Ini benefit alias-driven serving.

---

# 22. Apa yang tidak otomatis dilakukan Registry?

Registry tidak otomatis tahu:

- model fair atau tidak;
- business KPI bagus atau tidak;
- inference latency acceptable atau tidak;
- data quality safe atau tidak.

Registry manage lifecycle metadata/version.

Decision governance tetap kita design.

---

# 23. Run naming dan tags

Good run naming membantu UI readable.

Tags membantu filter.

Bad:

~~~text
run_123
run_124
~~~

Better context:

~~~text
hist-gradient-boosting
stage=initial-validation
~~~

Naming bukan core correctness, tapi operational usability matters.

---

# 24. Experiment failure scenario

Suppose baseline run logged, model training fail.

MLflow bisa punya partial history.

Itu okay.

Experiment tracking juga mencatat failure context tergantung implementation.

Jangan delete evidence hanya supaya UI terlihat bersih.

Failed runs bisa useful buat debugging.

---

# 25. MLflow state dan Git

Folder:

~~~text
.mlflow/
~~~

di-ignore Git.

Kenapa?

Itu runtime tracking database/artifact state, bukan source.

Git track code/config.

MLflow track experiment state.

Again, different responsibility.

---

# 26. Mini challenge

Tanpa lihat docs, trace prediction model production:

~~~text
champion alias
→ ?
→ ?
→ dataset SHA
~~~

Expected:

~~~text
champion alias
→ model version
→ source MLflow run
→ dataset metadata/SHA
~~~

Kalau chain ini natural, Model Registry concept sudah masuk.

---

# 27. What if model kalah baseline?

Tracked run tetap valuable.

Jangan delete.

MLflow menunjukkan evidence bahwa attempt tidak improve baseline.

Training DAG later bisa decide:

~~~text
model_beats_baseline = false
↓
do not register challenger
~~~

Tracking dan promotion adalah separate stages.

---

# 28. Checkpoint

1. Kenapa start_mlflow helper dibuat?
2. Tracking URI buat apa?
3. Experiment vs Run?
4. Parameter vs Metric?
5. Tag vs Artifact?
6. Kenapa baseline ikut dilog?
7. Dataset SHA connect Step 3 ke MLflow bagaimana?
8. Run ID role-nya apa?
9. Tracking run dan Registry model version relation?
10. Kenapa default alias challenger?
11. Champion alias solve hard-coded version bagaimana?
12. Rollback model concept-nya apa?
13. Kenapa .mlflow tidak masuk Git?
14. Model kalah baseline masih perlu dicatat kenapa?

Kalau semua clear, kalian sudah punya traceability dari data snapshot sampai production model alias.

Next kita orchestrate workflow-nya di Airflow.
