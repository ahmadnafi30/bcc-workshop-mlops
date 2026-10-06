# Step 3 — DVC: Membekukan Training Data Biar Experiment Nggak “Pakai File yang Mana Ya?”

Sampai Step 2 kita sudah punya feature dataset dan model yang bisa ditrain.

Sekarang coba bayangin satu minggu ke depan.

Feature dataset bertambah karena Jan 27, Jan 28, Jan 29 masuk.

File yang sama:

~~~text
data/features/taxi_demand_features.parquet
~~~

content-nya berubah.

Lalu kita tanya:

> “Model initial yang kita train kemarin sebenarnya pakai rows sampai tanggal berapa?”

Kalau jawabannya cuma:

> “Pakai file features itu.”

belum cukup.

Kita perlu training input yang **frozen dan identifiable**.

Nah, di step ini DVC masuk.

---

## Goal

Setelah selesai kalian harus bisa menjelaskan:

- kenapa moving feature file bukan training identity yang bagus;
- apa itu training snapshot;
- anatomy dvc.yaml;
- cmd, deps, outs;
- apa yang terjadi saat dvc repro;
- kenapa DVC cache bukan Git;
- kenapa SHA fingerprint juga dicatat;
- kenapa DVC dan MLflow punya responsibility beda;
- apa yang berubah kalau dependency berubah.

---

# 1. Lihat dulu feature dataset yang sekarang ada

Pastikan:

~~~text
data/features/taxi_demand_features.parquet
~~~

sudah exist.

Optional inspect:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/features/taxi_demand_features.parquet'); print(df.shape); print(df['timestamp'].min()); print(df['timestamp'].max())"
~~~

Pertanyaan:

> “Kalau besok file ini ditambah Jan 27, apakah nama filenya berubah?”

No.

Itu source of ambiguity.

---

# 2. Buat snapshot manual dulu

Sebelum DVC, jalankan underlying script:

~~~bash
uv run python scripts/create_training_snapshot.py --cutoff-date 2025-01-26
~~~

Output:

~~~text
data/snapshots/training/taxi_demand_2025-01-26.parquet
~~~

Terminal juga print:

~~~text
file
rows
zones
sha256
~~~

Pause.

Kenapa nama file punya cutoff date?

Karena kita ingin identity yang readable.

Kenapa masih butuh SHA kalau nama sudah ada?

Karena filename bisa sama tapi content bisa berubah kalau overwrite.

Readable identity + content fingerprint lebih kuat.

---

# 3. Apa yang dilakukan script snapshot?

Actual flow:

~~~text
read feature dataset
↓
filter rows <= cutoff date
↓
create snapshot
↓
build deterministic snapshot name
↓
write Parquet
↓
describe snapshot
↓
calculate SHA256
~~~

Important: cutoff date menentukan **data mana yang boleh masuk training context**.

Snapshot bukan copy arbitrary.

Dia punya temporal boundary.

---

# 4. Open dvc.yaml

File:

---

Actual stage kita sederhana:

~~~yaml
stages:
  create_training_snapshot:
    cmd: python scripts/create_training_snapshot.py --cutoff-date 2025-01-26
    deps:
      - data/features/taxi_demand_features.parquet
      - scripts/create_training_snapshot.py
      - src/data_versioning/snapshot.py
    outs:
      - data/snapshots/training/taxi_demand_2025-01-26.parquet
~~~

Jangan hafal YAML.

Baca seperti kalimat.

---

# 5. cmd — “Kalau perlu reproduce, jalankan apa?”

~~~text
cmd
→ python scripts/create_training_snapshot.py ...
~~~

DVC perlu tahu command yang menghasilkan output.

Jadi DVC bukan magic yang tahu sendiri cara membuat snapshot.

Kita yang declare recipe-nya.

---

# 6. deps — “Apa yang bisa mengubah hasil?”

Dependencies:

~~~text
feature dataset
snapshot script
snapshot implementation
~~~

Kenapa source code masuk deps?

Karena output bisa berubah walaupun input data sama kalau logic snapshot berubah.

Reproducibility bukan cuma data dependency.

Code dependency matters.

---

# 7. outs — “Artifact apa yang dihasilkan?”

Output:

~~~text
taxi_demand_2025-01-26.parquet
~~~

DVC track state artifact ini.

Mental model:

~~~text
deps
+
cmd
↓
outs
~~~

Ini mirip build system.

---

# 8. Sebelum dvc repro, predict behavior

Suppose snapshot sudah ada dan dependency belum berubah.

Apa yang kalian expect?

~~~text
DVC
→ stage up-to-date
→ tidak perlu regenerate unnecessarily
~~~

Sekarang run:

~~~bash
uv run dvc repro create_training_snapshot
~~~

Observe output.

Jangan cuma lihat command selesai.

Cari apakah stage rerun atau dianggap unchanged.

---

# 9. dvc status

Run:

~~~bash
uv run dvc status
~~~

Goal:

> “Apakah current pipeline output masih sesuai dependency state?”

Kalau feature dataset berubah, DVC bisa report stage out-of-date.

Itu jauh lebih useful daripada manusia mengingat:

> “Kayaknya kemarin file berubah deh.”

---

# 10. Experiment kecil: dependency berubah

Kalau workshop environment aman dan presenter punya backup, bisa demo conceptual change.

Misalnya feature dataset rebuilt setelah new date.

Sekarang:

~~~text
dep hash changes
↓
DVC detects stage stale
↓
dvc repro reruns snapshot stage
~~~

Jangan edit snapshot output manual lalu menganggap pipeline valid.

Output seharusnya berasal dari declared recipe.

---

# 11. DVC cache

DVC punya local cache:

~~~text
.dvc/cache/
~~~

Kenapa cache?

Supaya data content tidak perlu disimpan berulang secara naive.

Git menyimpan source + metadata.

DVC cache menyimpan heavy data content.

Separation:

~~~text
Git
→ project history

DVC
→ data artifact state/cache
~~~

---

# 12. “Kalau cache lokal, teammate lain dapat datanya gimana?”

Good question.

Production/team usage biasanya pakai DVC remote.

Concept:

~~~text
local DVC cache
↓
dvc push
↓
shared remote storage
↓
teammate dvc pull
~~~

Remote bisa object storage atau supported backend lain.

Workshop tidak setup remote karena credential/cloud setup akan mengalihkan fokus.

Tapi architecture path-nya jelas.

---

# 13. Kenapa snapshot folder tidak masuk Git normal?

Parquet binary bisa cukup besar.

Kalau setiap snapshot di-commit directly ke Git:

~~~text
repo size grows
binary diff poor
clone heavy
~~~

Git bukan ideal storage buat repeatedly changing large ML data artifact.

DVC memberi metadata-driven approach.

---

# 14. DVC vs .gitignore

Generated data directory di-ignore Git.

Apakah berarti data “nggak versioned”?

Not necessarily.

Git ignore hanya bilang Git tidak store file binary directly.

DVC pipeline metadata/fingerprint bisa tetap represent artifact state.

Version control system dan artifact storage dipisahkan.

---

# 15. Snapshot immutability mindset

Kalau snapshot:

~~~text
taxi_demand_2025-01-26.parquet
~~~

sudah dipakai training, healthy behavior:

~~~text
jangan diam-diam edit
~~~

Kalau data sampai Feb 10:

~~~text
buat snapshot baru
taxi_demand_2025-02-10.parquet
~~~

Ini menjaga old model lineage.

---

# 16. SHA256 — coba pikir kenapa useful

Terminal print SHA.

Suppose dua machine punya file:

~~~text
taxi_demand_2025-01-26.parquet
~~~

Nama sama.

SHA sama?

Kalau iya, strong evidence content sama.

Kalau beda, content beda.

MLflow nanti log SHA ini.

Jadi:

~~~text
DVC snapshot
↓
SHA fingerprint
↓
MLflow run metadata
~~~

Cross-tool lineage mulai terbentuk.

---

# 17. DVC vs MLflow — jangan jawab “sama-sama versioning”

DVC fokus:

> “Bagaimana data artifact ini direproduce dari dependencies?”

MLflow fokus:

> “Experiment run ini menggunakan configuration/data/model apa dan hasilnya bagaimana?”

Contoh:

~~~text
DVC:
snapshot X up-to-date?

MLflow:
run Y memakai snapshot X, MAE berapa?
~~~

Tools-nya complement.

---

# 18. DVC vs Airflow

DVC bisa punya pipeline stage.

Airflow juga workflow.

Apakah redundant?

Tidak persis.

DVC strong di:

- data/artifact dependency;
- reproducibility;
- content tracking.

Airflow strong di:

- orchestration;
- scheduling;
- task state;
- retries;
- distributed workflow control.

Project kita bahkan punya Airflow training task yang menjalankan:

~~~text
dvc repro
~~~

Artinya orchestrator memanggil reproducibility tool.

---

# 19. Failure scenario

Suppose feature dataset belum ada.

Run snapshot script.

Expected:

~~~text
FileNotFoundError
→ build_features dulu
~~~

Bagus.

Kenapa?

Karena snapshot task punya explicit dependency.

Pipeline tidak silently membuat empty snapshot.

---

# 20. Mini challenge

Coba jawab apa yang harus berubah di dvc.yaml kalau snapshot cutoff jadi Feb 10.

Possible:

~~~text
cmd cutoff
output filename
~~~

Tapi jangan edit initial stage sembarangan kalau ingin preserve old state.

Production design bisa parameterize/multiple stages.

Workshop initial DVC stage sengaja static supaya concept mudah.

Runtime retraining nanti punya separate snapshot behavior.

---

# 21. Checkpoint

1. Moving feature file kenapa bukan identity training yang kuat?
2. Snapshot artinya apa?
3. cutoff-date solve apa?
4. cmd, deps, outs masing-masing?
5. Kenapa code file masuk deps?
6. dvc repro beda apa dengan langsung python script?
7. dvc status jawab pertanyaan apa?
8. Cache dan remote beda apa?
9. Kenapa Parquet snapshot tidak masuk Git biasa?
10. SHA256 membantu lineage bagaimana?
11. DVC dan MLflow beda responsibility?
12. DVC dan Airflow bisa dipakai bareng kenapa?
13. Kenapa old snapshot sebaiknya immutable?

Kalau bisa jawab, DVC sudah lebih dari “Git buat data” di kepala kalian.

Next kita pakai snapshot tersebut untuk experiment yang dicatat proper lewat MLflow.
