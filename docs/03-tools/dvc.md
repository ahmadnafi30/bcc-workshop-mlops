# DVC — Git Buat Data? Kurang Lebih, Tapi Jangan Salah Paham

Kalau baru dengar DVC, orang sering bilang:

> “Oh, ini Git buat data ya?”

Boleh dipakai sebagai first intuition, tapi sebenarnya kalau berhenti di situ agak misleading.

DVC bukan replacement Git. DVC justru kerja **bareng Git** supaya project ML bisa punya data lineage yang lebih jelas.

---

## Problem yang kita punya

Bayangin kita sudah train model pertama.

Input-nya:

~~~text
data/features/taxi_demand_features.parquet
~~~

Model bagus. Kita save metric.

Seminggu kemudian, feature file itu berubah karena ada data baru.

Nama file-nya tetap sama.

~~~text
taxi_demand_features.parquet
~~~

Sekarang pertanyaannya:

> “Model version 1 dulu train pakai content file yang mana?”

Filename aja nggak cukup.

Kalau file overwrite terus, history content-nya hilang.

Git sebenarnya bisa version file, tapi large binary data seperti Parquet bukan use case ideal untuk Git history. Repository bisa cepat bengkak dan diff binary juga nggak meaningful.

Di sinilah DVC mulai useful.

---

## Analogi: resep dan batch bahan

Bayangin Git track resep.

~~~text
recipe_v3.py
~~~

Tapi hasil masakan bukan cuma dipengaruhi resep. Bahan yang dipakai juga matters.

Misalnya tepung batch hari ini beda dengan batch minggu lalu.

Kalau hasil eksperimen berubah, kita pengen tahu:

~~~text
recipe version mana?
+
ingredient batch mana?
~~~

Mapping ke ML:

~~~text
Git
→ code / recipe version

DVC
→ data artifact / ingredient batch

MLflow
→ experiment result
~~~

Nah, ini kenapa Git, DVC, MLflow sering muncul bareng tapi punya responsibility beda.

---

## Apa yang kita version di workshop ini?

Kita fokus ke **training snapshot**.

Contoh:

~~~text
data/snapshots/training/
└── taxi_demand_2025-01-26.parquet
~~~

Kenapa snapshot, bukan semua raw TLC data?

Karena untuk workshop, pertanyaan reproducibility yang paling penting adalah:

> “Model ini train dari exact model-ready dataset yang mana?”

Raw TLC source bisa didownload ulang dari official source. Yang paling dekat dengan training adalah snapshot setelah feature engineering.

Di production besar, kalian bisa version lebih banyak layer. Tapi buat belajar lifecycle, snapshot ini sudah cukup meaningful.

---

## Apa itu snapshot?

Snapshot di sini bukan screenshot.

Snapshot = frozen view dari training data pada cutoff tertentu.

Misalnya:

~~~text
cutoff = 2025-01-26
~~~

Artinya snapshot berisi feature rows yang available sampai tanggal tersebut.

Kenapa perlu freeze?

Karena feature dataset utama nanti terus berkembang saat Jan 27, Jan 28, dan seterusnya masuk.

Kalau training selalu baca “latest file”, kita kehilangan ability buat recreate experiment lama.

Snapshot bikin input training lebih stable.

---

## dvc.yaml itu apa?

Open file:

~~~text
dvc.yaml
~~~

Kita punya stage:

~~~text
create_training_snapshot
~~~

Mental model DVC stage:

~~~text
cmd
→ command apa yang menghasilkan output?

deps
→ input apa yang mempengaruhi output?

outs
→ output apa yang dihasilkan?
~~~

Jadi DVC tidak cuma tahu file output.

Dia tahu relationship.

Conceptually:

~~~text
feature dataset
      +
snapshot code
      +
snapshot script
      ↓
create_training_snapshot
      ↓
training snapshot
~~~

Kalau dependency berubah, DVC tahu stage bisa jadi perlu dijalankan ulang.

---

## dvc repro

Command:

~~~bash
uv run dvc repro create_training_snapshot
~~~

Artinya kurang lebih:

> “Pastikan stage ini up-to-date. Kalau input berubah, reproduce output-nya.”

Ini beda dengan sekadar:

~~~bash
python create_training_snapshot.py
~~~

Python command cuma run.

DVC punya state awareness.

Dia tahu dependency dan output.

---

## DVC cache

DVC biasanya menyimpan content di cache lokal:

~~~text
.dvc/cache/
~~~

Kenapa cache?

Supaya DVC nggak perlu duplikasi full data untuk setiap state secara naive.

Metadata yang ringan bisa masuk Git, sementara heavy data content dikelola terpisah.

---

## DVC remote — kenapa workshop belum pakai?

Di team production, local cache doang nggak cukup.

Kalau laptop kalian mati, data cache hilang.

Biasanya DVC connect ke remote storage:

~~~text
S3
GCS
Azure Blob
SSH
other supported remote
~~~

Lalu workflow-nya bisa:

~~~text
dvc push
dvc pull
~~~

Kenapa kita nggak setup remote sekarang?

Karena remote berarti credential, cloud config, IAM, dan extra failure point.

Untuk workshop core, kita fokus dulu ke **concept of reproducible data artifact**.

Setelah concept-nya paham, remote cuma extension infrastructure.

---

## DVC vs Git LFS

Kadang ada pertanyaan:

> “Kenapa nggak Git LFS aja?”

Git LFS bagus buat large files yang tetap mengikuti Git object workflow.

DVC lebih opinionated untuk data/ML pipeline, dependency graph, repro stage, dan data artifacts.

Bukan berarti satu selalu lebih baik.

Pertanyaannya balik ke use case.

Workshop ini ingin ngajarin:

~~~text
data pipeline dependency
+
training snapshot reproducibility
~~~

makanya DVC cocok.

---

## DVC vs MLflow

Ini harus jelas.

### DVC

Jawab:

> “Data state yang menghasilkan training input ini apa?”

### MLflow

Jawab:

> “Experiment run ini parameter, metric, artifact, dan context-nya apa?”

Kita bahkan log snapshot metadata ke MLflow:

~~~text
dataset_snapshot
dataset_sha256
dataset_rows
dataset_zones
~~~

Jadi lineage chain:

~~~text
DVC snapshot
      ↓
MLflow run
      ↓
model artifact
      ↓
registered version
~~~

Nah, ini mulai terasa MLOps-nya.

---

## Hash itu buat apa?

Project kita calculate SHA256 dari snapshot.

Kenapa?

Karena filename bukan identity yang kuat.

Dua file bisa sama-sama bernama:

~~~text
taxi_demand_2025-01-26.parquet
~~~

tapi content-nya beda kalau seseorang overwrite file.

Hash membantu identify content.

Kalau hash berubah, content berubah.

---

## Common mistake: version everything tanpa tujuan

Jangan karena punya DVC lalu semua folder di-track.

Tanya:

> “Artifact mana yang penting buat reproducibility model?”

Too much tracking bisa bikin workflow ribet.

Too little tracking bikin lineage hilang.

Design-nya harus purposeful.

---

## Common mistake: mutable snapshot

Kalau snapshot sudah dipakai train model, jangan edit diam-diam.

Lebih sehat:

~~~text
old snapshot
→ keep

new data
→ new snapshot
~~~

Jadi lineage model lama tetap valid.

---

## Checkpoint

Coba jawab tanpa buka docs:

1. Kenapa Git aja belum cukup buat data ML?
2. Apa bedanya feature dataset aktif dan training snapshot?
3. DVC stage punya cmd, deps, outs — masing-masing artinya apa?
4. Kenapa DVC dan MLflow nggak redundant?
5. Kenapa hash snapshot useful?

Kalau bisa jawab, kalian sudah paham DVC jauh lebih dalam daripada sekadar “Git for data”.
