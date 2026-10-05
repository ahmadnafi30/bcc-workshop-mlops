# Workshop Overview

## Sebelum ngomongin tools, kita samakan cerita dulu

Hi peers!

Di section ini kita belum akan install Airflow, belum buka MLflow, dan belum ngomongin Docker.

Kenapa?

Karena kalau workshop dimulai dengan:

~~~text
pip install airflow
docker compose up
mlflow server
~~~

besar kemungkinan yang kalian ingat setelah pulang cuma command-command random.

Kita mau kebalikannya.

Kita pengen nanti saat melihat tool, kalian bisa bilang:

> “Oh iya, tool ini muncul karena tadi ada problem itu.”

Jadi di halaman ini kita lihat dulu big picture-nya.

---

# Project yang kita bangun

Kita akan membuat system yang memprediksi demand Yellow Taxi di Manhattan satu jam ke depan.

Misalnya:

~~~text
Current time:
17:00

Taxi Zone:
161

Target:
18:00

Prediction:
148 pickups
~~~

Di balik satu prediction sesederhana itu ternyata banyak hal yang harus terjadi.

Model butuh historical data.

Historical data harus diproses.

Feature harus dibentuk dengan benar.

Model harus ditrain.

Eksperimen perlu dicatat.

Model terbaik perlu dipilih.

Application perlu akses prediction.

System perlu dimonitor.

Dan nanti ketika performa turun, kita perlu decide apakah retraining perlu dilakukan.

Itulah kenapa project ini cocok buat belajar MLOps end-to-end.

---

# Siapa target audience workshop ini?

Workshop ini cocok untuk kalian yang sudah pernah sedikit menyentuh Machine Learning, tapi mungkin workflow-nya masih seperti:

~~~text
notebook
↓
train
↓
metric
↓
save model
↓
selesai
~~~

Kalian minimal cukup familiar dengan:

- Python,
- Pandas,
- train/validation split,
- model.fit(),
- model.predict(),
- regression metric seperti MAE.

Kalian **nggak perlu** sudah ngerti:

- Docker,
- Airflow,
- DVC,
- MLflow,
- FastAPI,
- Prometheus,
- Grafana,
- GitHub Actions.

Semua akan kita bangun gradually.

---

# What will you learn?

Setelah workshop, target-nya bukan supaya kalian hafal syntax semua tools.

Target-nya lebih ke kalian bisa menjawab pertanyaan seperti:

> Kenapa Git saja belum cukup buat tracking ML experiment?

> Bedanya DVC dan MLflow apa?

> DAG itu sebenarnya apa?

> Kenapa logic preprocessing sebaiknya nggak ditaruh semua di DAG?

> Model Registry buat apa kalau kita sudah punya file model?

> Kenapa serving code load champion alias, bukan hard-code version?

> Bedanya monitoring API dan monitoring model apa?

> Kalau MAE production naik, apakah model harus langsung diganti?

Kalau kalian bisa explain pertanyaan-pertanyaan itu dengan bahasa sendiri, workshop ini berhasil.

---

# Kita akan membangun ini secara bertahap

## Stage 1 — Data dulu

Kita ambil NYC Yellow Taxi Trip Records.

Raw data bentuknya:

~~~text
1 row = 1 taxi trip
~~~

Tapi model kita butuh:

~~~text
1 row = 1 taxi zone × 1 hour
~~~

Jadi data harus di-aggregate dulu.

---

## Stage 2 — Train model tanpa MLOps tools

Kita sengaja **tidak langsung pakai MLflow**.

Kita bikin dulu workflow ML normal:

~~~text
load data
↓
build features
↓
split train / validation
↓
baseline
↓
train ML model
↓
calculate MAE
~~~

Kenapa?

Supaya kalian merasakan dulu limitation-nya.

Kalau dari awal semua sudah otomatis, susah ngerti kenapa automation itu useful.

---

## Stage 3 — DVC masuk saat kita mulai bertanya soal data

Misalnya model kita bagus.

Terus dua minggu kemudian data berubah.

Kita train ulang.

Pertanyaannya:

> “Model version sebelumnya sebenarnya pakai data yang mana?”

Nah, di sini kita mulai butuh training snapshot yang reproducible.

Masuklah DVC.

---

## Stage 4 — MLflow masuk saat eksperimen mulai banyak

Awalnya:

~~~text
run 1
run 2
run 3
~~~

Masih bisa dicatat manual.

Nanti jadi:

~~~text
model A
model B
different params
different snapshots
different metrics
different artifacts
~~~

Mulai ribet.

MLflow membantu kita record experiment secara structured.

---

## Stage 5 — Model Registry masuk saat eksperimen berubah jadi candidate

Ada perbedaan besar antara:

> “Model ini punya MAE bagus.”

dan:

> “Model ini sudah approved buat dipakai application.”

Model Registry membantu kita punya konsep:

~~~text
challenger
champion
~~~

Jadi model lifecycle lebih jelas.

---

## Stage 6 — Airflow masuk saat manual steps mulai repot

Kita akan punya flow:

~~~text
release daily batch
↓
validate
↓
aggregate
↓
build features
~~~

dan flow lain:

~~~text
snapshot
↓
train
↓
register
~~~

Kalau semua manual terus, lama-lama:

> “Tadi step yang mana sudah dijalankan?”

Airflow masuk buat orchestration.

---

## Stage 7 — FastAPI masuk saat model perlu dipakai system lain

Python object model hanya bisa dipakai langsung dari Python process.

Application lain lebih nyaman punya interface:

~~~http
POST /predict
~~~

FastAPI menjadi boundary antara ML logic dan external client.

---

## Stage 8 — Docker masuk karena environment harus konsisten

Klasik banget:

> “Di laptopku jalan.”

Terus laptop orang lain:

> “Kok error?”

Docker membantu kita package runtime environment.

Bukan berarti semua masalah hilang, tapi environment jadi jauh lebih controlled.

---

## Stage 9 — CI/CD masuk karena perubahan code perlu quality gate

Kita mulai punya repo yang cukup kompleks.

Kalau ada perubahan:

- tests harus jalan,
- lint harus lolos,
- docs jangan rusak,
- Docker harus masih bisa build.

GitHub Actions otomatis ngecek itu.

---

## Stage 10 — Monitoring masuk setelah system hidup

Model yang sudah diserve belum berarti selesai.

Kita perlu tahu dua hal:

~~~text
Is the system healthy?
and
Is the model still good?
~~~

Prometheus + Grafana bantu operational monitoring.

Prediction log + ground truth evaluation bantu model performance monitoring.

---

## Stage 11 — Retraining

Kalau recent performance memburuk:

~~~text
recent MAE
>
reference MAE × threshold
~~~

system bisa create new training snapshot, retrain, lalu register challenger.

Tapi kita tidak otomatis promote ke champion.

Kenapa?

Karena:

> **Automatic retraining tidak harus berarti automatic production promotion.**

Itu governance decision yang beda.

---

# Kenapa project ini sengaja “production-like”, bukan “production-grade”?

Ini juga penting.

Workshop ini bukan mau pura-pura bahwa architecture lokal kita sama persis dengan system production skala besar.

Kita masih pakai simplification seperti:

- local files,
- SQLite,
- Airflow standalone,
- Docker Compose,
- manual champion approval.

Kenapa nggak langsung Kubernetes, S3, Terraform, Kafka, feature store, dsb?

Karena tujuan pertama kita adalah memahami lifecycle.

Kalau lifecycle-nya belum paham tapi infrastructure-nya langsung super kompleks, kita malah belajar debugging platform, bukan MLOps.

Jadi philosophy-nya:

~~~text
Understand the concept first.
Scale the infrastructure later.
~~~

---

# Alur belajar yang kita pakai

Setiap tool akan dibahas dengan pattern yang sama:

### 1. Problem

Apa yang bikin workflow sebelumnya kurang enak?

### 2. Concept

Secara konsep kita butuh apa?

### 3. Tool

Baru kita lihat tool yang dipakai.

### 4. Project implementation

Tool itu masuk di bagian mana dari repo?

### 5. Hands-on

Kita jalanin.

### 6. Checkpoint

Apa yang harus kalian pahami sebelum lanjut?

Dengan pattern ini, harapannya workshop terasa seperti satu cerita panjang, bukan sebelas mini tutorial yang nggak nyambung.
