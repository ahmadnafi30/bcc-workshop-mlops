# MLflow Model Registry — Experiment Bagus Belum Tentu Langsung Production
!!! tip "Registry UI: dari candidate ke model yang dipakai"
    Di MLflow, buka **Models** lalu pilih **taxi-demand-forecasting-model**. Periksa version dan source run untuk menelusuri asal model. Alias **challenger** adalah candidate review; alias **champion** adalah pilihan yang dibaca API. Tidak semua run otomatis terdaftar atau dipromosikan. Lihat [tur Registry untuk pemula](../00-start-here.md#registry-ui) dan jangan promote sebelum membandingkan hasilnya.



Ini transition penting.

Kita sudah punya experiment tracking.

Ada run bagus.

Pertanyaannya:

> “Apakah run bagus itu langsung jadi production model?”

Jawabannya: belum tentu.

Tracking dan serving punya lifecycle boundary.

Model Registry masuk buat manage **model versions yang dianggap candidate untuk dipakai**.

---

## Analogi: audition vs cast utama

Bayangin film.

Ada banyak orang ikut audition.

Itu experiment runs.

Beberapa orang bagus dan masuk shortlist.

Itu registered model versions.

Satu orang akhirnya dipilih jadi pemeran utama.

Itu champion.

Candidate yang lagi diuji bisa disebut challenger.

Jadi:

~~~text
experiment run
≠
automatically production
~~~

---

## Registered Model

Kita punya logical model name:

~~~text
taxi-demand-forecasting-model
~~~

Di bawah nama itu ada version:

~~~text
version 1
version 2
version 3
...
~~~

Setiap version bisa trace balik ke source MLflow run.

---

## Kenapa versioning?

Kalau model baru datang, kita tidak overwrite model lama diam-diam.

Kita punya:

~~~text
v1
v2
v3
~~~

Benefit:

- audit,
- comparison,
- rollback,
- promotion history.

---

## Alias

Project kita pakai alias:

~~~text
challenger
champion
~~~

Alias itu pointer.

Contoh:

~~~text
champion
↓
version 3
~~~

Besok setelah review:

~~~text
champion
↓
version 5
~~~

Serving code tetap request:

~~~text
champion
~~~

Dia nggak perlu hard-code version number.

---

## Kenapa alias lebih baik dari hard-coded version?

Bad:

~~~text
API loads version 3
~~~

Setiap promotion:

~~~text
edit code
commit
deploy
~~~

Padahal yang berubah cuma model selection.

Dengan alias:

~~~text
API loads champion
~~~

Model governance dan application source lebih loosely coupled.

---

## Challenger

Challenger = candidate baru.

Misalnya retraining menghasilkan model yang beat baseline.

Kita register sebagai challenger.

Kenapa belum champion?

Karena threshold internal training belum tentu cukup buat automatic production approval.

Mungkin kita masih mau review:

- validation period,
- recent production MAE,
- feature distribution,
- data quality,
- business constraint.

---

## Champion

Champion = model yang approved untuk serving.

Project kita sengaja manual promotion.

Command:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

Kenapa manual?

Bukan karena automation jelek.

Tapi karena workshop mau menunjukkan governance boundary:

~~~text
automatic retraining
≠
automatic production promotion
~~~

Dua decision itu bisa punya risk level berbeda.

---

## Rollback

Suppose v5 jadi champion lalu ternyata behavior jelek.

Kalau v3 masih ada, alias bisa diarahkan balik.

Mental model:

~~~text
champion pointer
v5
↓
move back
↓
v3
~~~

Lebih clean daripada restore random file backup.

---

## Lineage chain

Ini salah satu bagian paling powerful.

~~~text
champion
↓
model version
↓
source MLflow run
↓
metrics + params
↓
dataset snapshot + SHA
~~~

Kalau ada pertanyaan:

> “Production prediction ini berasal dari model apa?”

kita bisa trace.

MLOps bukan cuma automation. Traceability juga sangat penting.

---

## Registry bukan model storage doang

Kalau kalian cuma lihat Registry sebagai tempat save file model, kalian kehilangan bagian governance-nya.

Registry membantu manage:

- version identity,
- alias,
- lineage,
- lifecycle state.

Model file bisa saja physically stored di artifact storage, tapi Registry memberi semantic management layer.

---

## Checkpoint

1. Tracking beda apa dengan Registry?
2. Kenapa experiment bagus nggak langsung production?
3. Version dan alias beda apa?
4. Challenger vs champion?
5. Kenapa manual promotion masih masuk akal?
6. Kalau champion baru jelek, rollback concept-nya gimana?
