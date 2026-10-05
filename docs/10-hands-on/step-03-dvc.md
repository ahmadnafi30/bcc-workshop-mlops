# Step 3 — DVC: Bikin Training Data Punya Identity

Sekarang kita punya snapshot.

Tapi kalau cuma file di folder, pertanyaan reproducibility masih ada.

> “File ini state yang mana? Kalau dependency berubah, gimana kita tahu harus rebuild?”

DVC masuk di sini.

---

## Goal

Setelah step ini:

- kalian ngerti stage dependency,
- bisa reproduce training snapshot,
- ngerti Git vs DVC,
- ngerti kenapa snapshot + hash masuk model lineage.

---

## 1. Buka dvc.yaml dulu

Jangan langsung run command.

Open file.

Cari:

~~~text
create_training_snapshot
~~~

Baca:

~~~text
cmd
deps
outs
~~~

Coba tebak meaning sebelum lanjut.

---

## 2. Translate ke bahasa manusia

~~~text
cmd
→ cara bikin output

deps
→ hal yang kalau berubah bisa mempengaruhi output

outs
→ artifact hasil stage
~~~

Ini seperti build recipe.

---

## 3. Run repro

~~~bash
uv run dvc repro create_training_snapshot
~~~

Observe output.

Kalau stage up-to-date, DVC bisa bilang nggak perlu rerun.

Kalau dependency berubah, stage reproduce.

---

## 4. Run status

~~~bash
uv run dvc status
~~~

Interpret result.

Kalau no changes, pipeline state aligned.

---

## 5. Run repro lagi

~~~bash
uv run dvc repro create_training_snapshot
~~~

Pertanyaan:

> “Kenapa tool reproducibility justru kadang tidak menjalankan command?”

Karena dia tahu output masih valid relatif terhadap dependencies.

---

## 6. Inspect cache

Lihat:

~~~text
.dvc/cache/
~~~

Jangan edit manual.

Itu internal data store.

---

## 7. Git thought experiment

Kalau snapshot Parquet 500 MB berubah 20 kali dan setiap version masuk Git normal, apa yang terjadi?

Repository history bisa bengkak.

DVC separate large content handling dari source history.

---

## 8. Hash connection

Project juga calculate SHA256 snapshot dan log ke MLflow.

Kenapa both DVC + SHA?

DVC manage pipeline artifact state.

SHA logged ke experiment memberi compact identity trace.

---

## 9. Mini challenge

Bayangin model version 7 punya MAE aneh.

Apa chain investigation?

~~~text
model v7
↓
MLflow run
↓
dataset snapshot name + hash
↓
DVC/data state
↓
feature code Git revision
~~~

Ini lineage thinking.

---

## Common mistake

Jangan edit snapshot lama yang sudah dipakai model.

Bikin snapshot baru.

Kalau old snapshot mutable, historical lineage jadi bohong.

---

## Checkpoint

Coba explain ke teman sebelah:

> “Kenapa DVC ada kalau kita sudah punya Git?”

Kalau jawabannya lebih detail dari “buat file besar”, bagus.

Next kita track experiment.
