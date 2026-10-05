# Workshop Overview — Kita Sebenarnya Lagi Bangun Apa Sih?

Hi peers 👋

Sebelum masuk ke DVC, Airflow, MLflow, Docker, Prometheus, dan teman-temannya, aku pengen kita punya satu mental model yang sama dulu. Karena kalau dari awal kita langsung dilempar ke tools, MLOps itu kelihatannya kayak kumpulan logo teknologi yang random banget. Hari ini belajar Airflow, besok MLflow, habis itu Docker, terus entah kenapa ada Grafana. Ujung-ujungnya kita hafal command, tapi pas ditanya **“kenapa sih tool ini dibutuhkan?”**, malah bingung.

Di workshop ini kita nggak mau belajar seperti itu.

Kita akan mulai dari satu project Machine Learning yang sangat normal. Ada data, ada feature engineering, ada model, ada metric. Baru setelah project itu mulai punya problem nyata, kita masukin satu tool untuk solve problem tersebut. Jadi urutannya bukan:

~~~text
Tool
↓
cari use case
~~~

tapi:

~~~text
Problem
↓
butuh capability apa?
↓
baru pilih tool
~~~

Itu mindset paling penting yang pengen kita bawa dari workshop ini.

---

## Use case kita: NYC Yellow Taxi Demand Forecasting

Sepanjang workshop kita cuma pakai **satu use case yang sama**, supaya semua materi terasa nyambung.

Goal-nya:

> **Predict berapa banyak pickup Yellow Taxi yang akan terjadi di setiap Manhattan taxi zone satu jam ke depan.**

Misalnya sekarang jam 17:00.

Kita pengen jawab:

~~~text
Zone 161
Target time: 18:00

Predicted demand:
147 pickups
~~~

Kenapa use case ini enak banget buat MLOps? Karena dia punya lifecycle yang cukup realistis. Data-nya time-based, ground truth datang belakangan, model bisa memburuk, prediction bisa dipakai application lain, ada alasan natural buat monitoring, dan ada alasan natural buat retraining.

Jadi kita nggak perlu bikin-bikin alasan kenapa monitoring dibutuhkan. Nanti kita benar-benar punya pertanyaan:

> “Model ini masih bagus nggak setelah beberapa hari dipakai?”

---

## Mulainya dari project ML biasa

Bayangin kalian Data Scientist dan project awalnya cuma:

~~~text
dataset
   ↓
feature engineering
   ↓
train model
   ↓
evaluate
   ↓
model.joblib
~~~

Kita punya result:

~~~text
Validation MAE = 10.2
~~~

Secara Machine Learning, ini valid banget. Kalau konteksnya tugas kuliah, Kaggle experiment, atau proof of concept, mungkin sudah cukup.

Tapi sekarang bayangin project ini mulai dipakai orang lain.

Backend engineer datang:

> “Modelnya dipanggil gimana?”

Manager nanya:

> “Model ini pakai data versi mana?”

Teman satu tim nanya:

> “Experiment yang MAE 10.2 itu parameter-nya apa?”

Ops engineer nanya:

> “Kalau service-nya error kita tahu dari mana?”

Sebulan kemudian:

> “Kok prediction-nya mulai jelek ya?”

Dan akhirnya:

> “Kalau memang jelek, retrain-nya kapan?”

Nah, mulai dari sini kita sudah keluar dari problem sekadar **training model**. Kita masuk ke problem:

> **How do we operate a Machine Learning system over time?**

Di situlah MLOps mulai meaningful.

---

## Lifecycle yang kita bangun

~~~text
NYC TLC Data
      ↓
Data Preparation
      ↓
Hourly Demand
      ↓
Feature Engineering
      ↓
Training Snapshot
      ↓
DVC
      ↓
Model Training
      ↓
MLflow Tracking
      ↓
Model Registry
      ↓
Airflow Orchestration
      ↓
FastAPI Serving
      ↓
Docker + Docker Compose
      ↓
GitHub Actions CI/CD
      ↓
Prometheus + Grafana
      ↓
Prediction Evaluation
      ↓
Retraining Decision
      ↓
New Challenger
      ↓
Review
      ↓
Champion
~~~

Kelihatannya panjang? Iya.

Tapi jangan dihafal.

Yang perlu kalian ingat cuma pola ini:

~~~text
setiap tool
harus punya problem
yang dia solve
~~~

Contohnya:

~~~text
"Dataset model ini exact-nya mana?"
↓
DVC

"Experiment kemarin parameter dan metric-nya apa?"
↓
MLflow

"Step A harus selesai sebelum B, terus kalau B gagal gimana?"
↓
Airflow

"Gimana backend request prediction?"
↓
FastAPI

"Works on my machine, di laptop lain error."
↓
Docker

"Setiap PR siapa yang ingetin run test?"
↓
GitHub Actions

"API hidup nggak? Latency-nya berapa?"
↓
Prometheus + Grafana

"Model masih akurat nggak?"
↓
Model monitoring
~~~

Dengan mental model kayak gini, tools jadi jauh lebih gampang dipahami.

---

## Analogi yang bakal sering kita pakai

Anggap **model itu resep**.

Kalian punya resep burger terbaik sedunia. Apakah resep itu otomatis jadi restoran? Ya nggak.

Kalian masih butuh bahan, supplier, kitchen workflow, quality control, waiter, inventory, monitoring, dan cara update menu.

| Restaurant | ML System |
| --- | --- |
| Recipe | Model |
| Ingredients | Data |
| Batch ingredients | Dataset snapshot |
| Cooking process | Training pipeline |
| Experiment notebook | MLflow |
| Approved menu | Model Registry |
| Waiter | FastAPI |
| Kitchen schedule | Airflow |
| Kitchen environment | Docker |
| Quality dashboard | Prometheus + Grafana |
| Update recipe | Retraining |

Analogi ini nggak 100% perfect, tapi useful banget buat satu ide:

> **Model itu cuma satu komponen dari ML system.**

Kalau workshop ini berhasil, kalian nggak lagi melihat training sebagai akhir project. Kalian mulai melihat dia sebagai salah satu step di lifecycle yang lebih panjang.

---

## Cara belajar yang kita pakai

Setiap materi kurang lebih akan mengikuti pola:

~~~text
problem dulu
↓
intuition
↓
analogy
↓
concept
↓
actual implementation project kita
↓
kenapa implementasinya begitu
↓
common mistake
↓
hands-on
↓
checkpoint
~~~

Jadi misalnya Airflow. Kita nggak mulai dari kalimat “DAG adalah Directed Acyclic Graph.” Kita mulai dari:

> “Kalian punya lima script yang harus jalan urut. Kalau script ketiga gagal, kalian tahu dari mana? Kalau perlu retry, ulang semua atau cuma step itu?”

Setelah problem-nya terasa, baru konsep DAG masuk.

---

## Production-like, bukan production copy-paste

Repo ini sengaja simplify beberapa hal:

- local filesystem,
- SQLite untuk MLflow metadata,
- Airflow standalone,
- Docker Compose,
- historical replay,
- manual champion approval.

Kenapa bukan langsung Kubernetes, S3, Kafka, feature store, Terraform, managed Airflow, dan cloud IAM? Karena kalau semua itu masuk sekaligus, kita malah sibuk setup infrastructure dan lupa lifecycle yang ingin dipelajari.

Nanti infrastructure bisa diganti:

~~~text
local file
→ object storage

Docker Compose
→ Kubernetes

standalone Airflow
→ managed Airflow

local MLflow
→ remote tracking server
~~~

Pattern lifecycle-nya tetap sama.

---

## Outcome yang kita cari

Target kita bukan:

> “Saya hafal command Airflow.”

Tapi:

> “Kalau workflow saya mulai punya dependency, retry, schedule, dan task failure, saya ngerti kenapa orchestrator dibutuhkan.”

Bukan:

> “Saya hafal Dockerfile.”

Tapi:

> “Saya ngerti kenapa packaging runtime membantu reproducibility.”

Bukan:

> “Saya bisa buka Grafana.”

Tapi:

> “Saya ngerti beda system health dengan model health.”

Kalau kalian bisa menjelaskan **why** dari tiap komponen, kalian sudah punya fondasi yang bagus banget buat belajar MLOps lebih jauh.
