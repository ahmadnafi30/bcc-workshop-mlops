# MLOps from Zero — Kenapa Machine Learning Butuh Lifecycle Sendiri?

Kalau kalian search “What is MLOps?” di internet, sering banget ketemu kalimat:

> MLOps is DevOps for Machine Learning.

Arah definisinya nggak salah. Tapi buat pemula, itu kadang belum membantu karena malah muncul pertanyaan baru: “DevOps aja belum terlalu ngerti, terus kenapa ML perlu versi khusus?”

Jadi kita mulai dari problem, bukan definisi.

---

## Project ML paling sederhana

Misalnya kalian punya:

~~~text
project/
├── notebook.ipynb
├── data.csv
└── model.pkl
~~~

Di notebook, kalian load data, train, evaluate, lalu save model.

Result:

~~~text
MAE = 10.2
~~~

Untuk experimentation, itu fine.

Problem baru muncul ketika model berubah dari:

> “Eksperimen saya.”

menjadi:

> “Something other people depend on.”

Begitu ada dependency ke orang atau system lain, requirement-nya ikut berubah.

---

## Problem pertama: reproducibility

Tiga minggu kemudian kalian buka folder data.

~~~text
data.csv
data_final.csv
data_fix.csv
data_fix_bener.csv
data_final_bener_2.csv
~~~

Relatable? 😭

Model yang MAE 10.2 tadi pakai yang mana?

Terus ternyata feature engineering pernah direvisi. Versi scikit-learn beda. Parameter pernah diganti. Random seed mungkin beda.

Jadi training context itu bukan cuma code.

~~~text
Code
+
Data
+
Parameters
+
Environment
+
Randomness
~~~

Kalau satu berubah, result bisa berubah.

Makanya kita butuh beberapa layer:

~~~text
Git
→ code history

DVC
→ training data snapshot

MLflow
→ experiment context

uv
→ environment consistency
~~~

Perhatikan bahwa tools ini saling melengkapi, bukan saling menggantikan.

---

## Problem kedua: deployability

Kalian punya file model. Backend developer tanya:

> “Cara aplikasi gue request prediction gimana?”

Kalau jawabannya:

> “Import file Python saya, load model, terus bikin lag feature manual.”

Technically bisa, tapi coupling-nya tinggi banget.

Backend jadi harus tahu model framework, feature order, lag logic, rolling window, model path, dan historical data.

Lebih clean kalau kita punya contract:

~~~http
POST /predict
~~~

Request:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Response:

~~~json
{
  "predicted_trip_count": 147.8
}
~~~

Client nggak perlu tahu internal model implementation. Itu abstraction boundary.

---

## Problem ketiga: observability

Sekarang API hidup.

HTTP 200. Latency 80 ms.

Apakah sistem sehat?

Belum tentu.

### Case A — API sehat, model jelek

~~~text
HTTP 200
latency 60 ms
zero server error
~~~

Tapi prediction meleset jauh terus-menerus.

Operationally sehat. Model-wise buruk.

### Case B — model bagus, service bermasalah

Model accuracy masih bagus, tapi API latency 15 detik dan request timeout.

Model-wise sehat. Service-wise buruk.

Jadi ML system punya minimal dua health dimension:

~~~text
System Health
+
Model Health
~~~

Ini konsep yang harus benar-benar kalian pegang.

---

## Problem keempat: maintainability

Data dunia nyata berubah.

Behavior berubah. Seasonality berubah. Business context berubah.

Contoh taxi:

~~~text
Training:
January

Later:
February / March
different traffic
different event
different demand pattern
~~~

Model yang bagus di January belum tentu bagus selamanya.

Jadi lifecycle production bukan:

~~~text
train
↓
deploy
↓
finish
~~~

lebih realistis:

~~~text
train
↓
deploy
↓
observe
↓
evaluate
↓
retrain if needed
↓
review
↓
promote
↓
observe again
~~~

Itu loop.

---

## Jadi MLOps itu apa?

Sekarang definisinya lebih meaningful.

Di workshop ini kita pakai definisi practical:

> **MLOps adalah practices dan engineering yang membuat lifecycle Machine Learning menjadi reproducible, deployable, observable, dan maintainable.**

Empat kata ini penting:

~~~text
reproducible
deployable
observable
maintainable
~~~

Kalau mau ingat MLOps, ingat empat itu.

---

## Kenapa ML beda dari software biasa?

Traditional software behavior mostly ditentukan code.

Machine Learning beda.

Behavior model dipengaruhi:

~~~text
code
data
features
parameters
library version
random seed
training process
~~~

Artinya source control code saja belum cukup menjelaskan output model.

Makanya ML engineering punya concern tambahan:

- dataset lineage,
- experiment tracking,
- model registry,
- model monitoring,
- retraining policy.

---

## Git vs DVC vs MLflow

Ini confusion yang super common.

### Git

Pertanyaan:

> “Code version yang mana?”

### DVC

Pertanyaan:

> “Training snapshot exact yang dipakai apa?”

### MLflow

Pertanyaan:

> “Run ini parameter, metric, artifact, dan dataset context-nya apa?”

Simplified:

~~~text
Git
→ what code?

DVC
→ what data?

MLflow
→ what experiment result?
~~~

Ketiganya nyambung.

---

## Airflow masuk di mana?

Bayangin pipeline:

~~~text
download
↓
validate
↓
aggregate
↓
features
↓
train
↓
evaluate
~~~

Kalau sekali jalan manual, gampang.

Kalau setiap hari? Kalau validate gagal? Kalau task kelima butuh output task ketiga? Kalau data belum datang?

Mulai terasa kita butuh orchestration.

Airflow coordinate workflow. Airflow bukan bikin model lebih pintar.

---

## Docker masuk di mana?

Project works di laptop kalian.

Di laptop teman:

~~~text
ModuleNotFoundError
different Python
missing system package
~~~

Classic.

Docker bantu package runtime environment.

Intuition-nya:

> “Daripada saya kasih list instalasi panjang, saya definisikan environment yang konsisten.”

Docker nggak solve bad model atau bad data. Dia solve environment consistency layer.

---

## CI/CD masuk di mana?

Setiap ada pull request, siapa yang memastikan test, lint, docs, dan Docker build jalan?

Kalau jawabannya:

> “Semoga contributor ingat.”

itu fragile.

GitHub Actions automate repository checks.

Perhatikan bedanya:

~~~text
code changed
→ CI/CD

model performance degraded
→ monitoring/retraining
~~~

Dua trigger yang berbeda.

---

## Monitoring masuk di mana?

Begitu service live, kita butuh feedback loop.

Operational feedback:

~~~text
request rate
latency
errors
service health
~~~

Model feedback:

~~~text
prediction
vs
actual
↓
MAE / RMSE
~~~

Tanpa feedback, production system seperti nyetir mobil tanpa dashboard. Mobilnya mungkin jalan, tapi kita nggak tahu kondisi mesin atau bensinnya.

---

## MLOps bukan checklist tools

MLOps bukan:

~~~text
Airflow ✅
Docker ✅
MLflow ✅
Grafana ✅
~~~

Kalau tools ada tapi training nggak reproducible, model nggak traceable, dan performance nggak dimonitor, tools tersebut cuma dekorasi architecture diagram.

Fokus kita adalah lifecycle. Tool cuma implementasi.
