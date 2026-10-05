# Step 3 — DVC: Making the Training Input Reproducible

Di Step 2 kita sudah punya snapshot.

Tapi sekarang kita mau naik level:

> “Bukan cuma punya file snapshot, tapi punya pipeline definition yang tahu input, command, dan output.”

Masuk DVC.

---

# 1. Open dvc.yaml

Jangan run command dulu.

Buka:

~~~text
dvc.yaml
~~~

Cari stage:

~~~text
create_training_snapshot
~~~

Coba identify:

~~~text
cmd
deps
outs
~~~

---

# 2. Tebak dulu artinya

## cmd

Menurut kalian?

Jawab:

> Command yang produce stage output.

## deps

> Input / source / code yang affect output.

## outs

> Artifact yang dihasilkan.

Kalau tiga concept ini clear, DVC stage sudah nggak terlalu misterius.

---

# 3. Reproduce

~~~bash
uv run dvc repro create_training_snapshot
~~~

Observe output.

Kalau dependencies unchanged, DVC bisa bilang stage up to date.

Kalau berubah, command rerun.

---

# 4. Run twice

Coba run lagi.

~~~bash
uv run dvc repro create_training_snapshot
~~~

Pertanyaan:

> Apakah stage rerun full kalau nothing changed?

Ini bagus buat lihat dependency-aware behavior.

---

# 5. Check status

~~~bash
uv run dvc status
~~~

Tujuan:

> Apakah pipeline output consistent dengan dependency state?

---

# 6. Inspect dvc.lock

Open:

~~~text
dvc.lock
~~~

Kalian nggak harus hafal format.

Cukup ngerti:

> Lock file menyimpan resolved pipeline state/checksum information.

---

# 7. Check cache

Folder:

~~~text
.dvc/cache/
~~~

Di-ignore Git.

Kenapa?

Heavy data content bukan Git history.

---

# 8. Coba ubah dependency secara mental

Misalnya feature data berubah karena Jan 27 masuk.

Apa yang harus terjadi?

~~~text
feature dependency changes
↓
DVC stage considered changed
↓
snapshot may need reproduce
~~~

Itulah dependency graph value.

---

# 9. Git + DVC

Coba bedakan:

~~~text
Git commit
→ dvc.yaml changed?
→ code changed?

DVC
→ data artifact changed?
~~~

Mereka pair.

---

# 10. DVC remote discussion

Workshop local only.

Coba bayangin teammate clone repo di laptop lain.

Mereka punya dvc.yaml tapi nggak punya cache data kalian.

Untuk team real, butuh DVC remote.

Contoh:

~~~text
S3
GCS
SSH
~~~

Kita intentionally belum configure credential.

---

# Mini challenge

Pertanyaan:

> Kenapa tidak commit taxi_demand_2025-01-26.parquet langsung ke Git?

Jawaban bukan:

> Karena dilarang.

Lebih tepat:

> Karena large/generated binary data punya lifecycle berbeda dari source code dan membuat Git history berat serta diff tidak meaningful.

---

# Checkpoint

Kalian harus bisa explain:

~~~text
Git
tracks source

DVC
tracks/reproduces data pipeline state

MLflow
tracks experiment
~~~

Next kita isi bagian ketiga: MLflow.
