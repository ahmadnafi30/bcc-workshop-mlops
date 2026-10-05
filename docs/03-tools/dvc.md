# DVC — Data Versioning Without Dumping Everything Into Git

## Sebelum DVC, kita sebenarnya sudah bisa train model

Misalnya kita punya:

~~~text
data/features/taxi_demand_features.parquet
~~~

Hari ini kita train model.

Besok data berubah.

Minggu depan kita retrain.

Lalu ada pertanyaan:

> “Model yang MAE-nya 10.2 itu pakai dataset yang mana?”

Kalian lihat folder.

Filename-nya masih:

~~~text
taxi_demand_features.parquet
~~~

Nah.

Di sinilah problem data lineage mulai muncul.

---

# Kenapa Git saja belum cukup?

Git sangat bagus buat:

- source code,
- text config,
- docs,
- YAML.

Tapi large binary data file bukan use case ideal Git.

Kalau setiap perubahan Parquet besar masuk Git history:

- repo cepat membengkak,
- diff tidak meaningful,
- cloning makin berat.

Jadi kita butuh cara lain buat manage data artifacts.

---

# DVC secara sederhana

DVC = Data Version Control.

Tapi jangan terlalu literal menganggap:

> “DVC adalah Git khusus data.”

Lebih useful kalau dipahami sebagai:

> **tool untuk mendefinisikan dependency data pipeline, track output artifact, dan reproduce state berdasarkan input yang berubah.**

DVC memang bekerja closely dengan Git, tapi responsibility-nya beda.

---

# Analogi bakery

Bayangin bakery.

Git menjawab:

> Recipe version mana yang dipakai?

DVC menjawab:

> Ingredient batch / prepared dough snapshot yang dipakai yang mana?

MLflow menjawab:

> Dari proses baking ini hasil quality score-nya berapa?

Jadi:

~~~text
Git
→ code history

DVC
→ data artifact state

MLflow
→ experiment history
~~~

---

# Apa yang kita version di workshop?

Kita nggak DVC-track semua raw TLC data.

Kita fokus ke **training snapshot**.

Contoh:

~~~text
data/snapshots/training/
taxi_demand_2025-01-26.parquet
~~~

Kenapa snapshot ini penting?

Karena ini input model yang sudah:

- processed,
- feature-engineered,
- frozen sampai cutoff date.

Jadi kalau model lahir dari snapshot Jan 26, kita punya referensi yang jelas.

---

# dvc.yaml

Open:

~~~text
dvc.yaml
~~~

Di sana ada stage:

~~~text
create_training_snapshot
~~~

Sebuah DVC stage biasanya punya tiga bagian penting.

## cmd

Command yang dijalankan.

## deps

Hal-hal yang affect output.

Misalnya:

~~~text
feature dataset
snapshot script
snapshot source code
~~~

## outs

Output stage.

Contoh:

~~~text
taxi_demand_2025-01-26.parquet
~~~

---

# Ini sebenarnya mirip build system

Coba lihat:

~~~text
input A
input B
script
  ↓
command
  ↓
output
~~~

DVC bisa decide:

> “Input berubah nggak?”

Kalau nggak:

> “No need to reproduce.”

Kalau berubah:

> “Stage perlu dijalankan lagi.”

Makanya DVC bukan sekadar file storage.

Dia punya pipeline dependency awareness.

---

# Run DVC stage

~~~bash
uv run dvc repro create_training_snapshot
~~~

Yang terjadi:

1. DVC baca stage definition.
2. Check dependencies.
3. Kalau perlu, run command.
4. Track output state.
5. Update lock metadata.

---

# dvc.lock

Setelah repro, kalian bisa lihat:

~~~text
dvc.lock
~~~

Lock file capture resolved state dari pipeline.

Jangan confuse dengan package lock.

~~~text
dependency lock
→ package environment

dvc.lock
→ data pipeline resolved state
~~~

Dua-duanya ngomong soal reproducibility, tapi domain berbeda.

---

# DVC cache

DVC menyimpan content artifact ke:

~~~text
.dvc/cache/
~~~

Cache ini nggak masuk Git.

Git hanya simpan lightweight metadata.

Jadi pattern-nya:

~~~text
Git
small metadata

DVC cache / remote
large data content
~~~

---

# Kenapa belum pakai DVC remote?

Dalam team beneran, local cache doang belum cukup.

Kalian butuh shared remote, misalnya:

~~~text
S3
GCS
Azure Blob
SSH storage
~~~

Tapi workshop sengaja belum pakai cloud credential.

Kenapa?

Karena kita mau understand:

- stage,
- dependency,
- output,
- cache,
- reproducibility.

Cloud remote adalah next infrastructure concern.

---

# Snapshot vs live features

Ini distinction penting.

~~~text
data/features/taxi_demand_features.parquet
~~~

bisa berubah saat daily data baru masuk.

Kalau training langsung terus pakai file live itu, experiment lama makin susah direproduce.

Makanya sebelum training:

~~~text
live features
↓
cutoff
↓
training snapshot
~~~

Snapshot harus dianggap immutable input untuk run tersebut.

---

# DVC + MLflow relation

Training snapshot juga kita fingerprint dengan SHA256.

MLflow log metadata:

~~~text
dataset_snapshot
dataset_sha256
dataset_rows
dataset_zones
~~~

Jadi nanti chain-nya:

~~~text
MLflow run
↓
dataset SHA
↓
training snapshot identity
↓
DVC pipeline
~~~

DVC dan MLflow saling melengkapi.

---

# Apa yang DVC tidak lakukan?

DVC bukan:

- experiment UI,
- model registry,
- API serving,
- scheduler,
- monitoring dashboard.

Kalau kalian mulai pakai DVC buat solve semua masalah, berarti responsibility-nya sudah campur.

---

# Workshop checkpoint

Setelah:

~~~bash
uv run dvc repro create_training_snapshot
~~~

kalian harus bisa answer:

> “Model nanti train dari dataset apa?”

Bukan:

> “Pokoknya dari features latest.”

Tapi:

~~~text
taxi_demand_2025-01-26.parquet
with a known fingerprint
~~~

Itulah value utamanya.
