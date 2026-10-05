# MLOps from Zero

## Jadi... MLOps itu sebenarnya apa?

Kalau cari definisi MLOps di internet, kalian bisa ketemu banyak versi.

Ada yang bilang:

> MLOps = DevOps for Machine Learning.

Ada yang bilang:

> MLOps is a set of practices for deploying and maintaining ML models reliably.

Keduanya nggak salah, tapi buat pemula kadang masih terasa abstrak.

Jadi di workshop ini kita pakai definisi yang lebih praktis:

> **MLOps adalah cara kita mengelola lifecycle Machine Learning supaya experiment-nya reproducible, model-nya bisa dipakai, system-nya bisa diamati, dan model-nya bisa dirawat setelah deployment.**

Coba fokus ke empat kata:

~~~text
reproducible
deployable
observable
maintainable
~~~

Kita bahas satu-satu.

---

# Mulai dari ML project biasa

Coba bayangin project ML yang mungkin pernah kalian buat:

~~~text
project/
├── notebook.ipynb
├── data.csv
└── model.pkl
~~~

Di notebook:

~~~python
df = pd.read_csv("data.csv")

model.fit(X_train, y_train)

pred = model.predict(X_test)

print(mae)
~~~

Hasil bagus.

~~~text
MAE = 10.2
~~~

Kalian save model.

Selesai.

Untuk experimentation, itu valid.

Problem baru muncul kalau model ini berubah dari:

> “Eksperimen saya.”

menjadi:

> “Something other people depend on.”

Begitu ada dependency ke orang lain atau system lain, pertanyaannya berubah.

---

# Problem pertama: reproducibility

Misalnya tiga minggu kemudian kalian buka lagi project.

Kalian menemukan:

~~~text
data.csv
data_final.csv
data_fix.csv
data_fix_bener.csv
data_final_bener_2.csv
~~~

Familiar? 😭

Model yang bagus tadi pakai yang mana?

Terus environment berubah.

Versi scikit-learn beda.

Feature engineering pernah direvisi.

Sekarang walaupun model file masih ada, kalian susah explain:

> “Model ini lahir dari kondisi apa?”

Reproducibility artinya kita ingin bisa reconstruct context dari experiment.

Kurang lebih kita perlu tahu:

~~~text
Code version
+
Data version
+
Parameters
+
Environment
=
Reproducible training context
~~~

Git membantu code version.

DVC membantu data snapshot.

MLflow membantu experiment metadata.

uv membantu environment consistency.

Mereka bukan saling menggantikan. Mereka saling melengkapi.

---

# Problem kedua: deployability

Model object di Python belum otomatis berguna untuk external application.

Misalnya backend developer nanya:

> “Gimana cara aplikasi gue minta prediction?”

Jawaban seperti:

> “Import file train.py terus load joblib ya.”

kurang ideal.

Lebih enak punya contract:

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

Sekarang external client nggak perlu tahu:

- model pakai sklearn,
- ada lag_168h,
- rolling window dibuat seperti apa,
- file model disimpan di mana.

Semua internal detail ditangani serving layer.

---

# Problem ketiga: observability

Anggap API sudah hidup.

Bisa diakses.

Request masuk.

Apakah berarti system sehat?

Belum tentu.

Ada dua kemungkinan:

### Case A

~~~text
API latency = 80 ms
HTTP 200
CPU normal
~~~

Tapi prediction MAE makin jelek.

Operationally sehat.

Model-wise rusak.

### Case B

Model sebenarnya masih bagus.

Tapi API latency 15 detik.

Request banyak timeout.

Model-wise sehat.

Operationally rusak.

Jadi ML system punya dua health dimension:

~~~text
System health
and
Model health
~~~

Ini salah satu konsep penting banget di MLOps.

Prometheus/Grafana lebih banyak bantu operational visibility.

Prediction log + delayed ground truth evaluation bantu model quality visibility.

---

# Problem keempat: maintainability

Data di dunia nyata berubah.

Behavior user berubah.

Seasonality berubah.

Business context berubah.

Model yang bagus hari ini belum tentu bagus selamanya.

Contoh taxi:

~~~text
Training period:
January

Later:
February / March
different traffic pattern
different event
different demand behavior
~~~

Suatu saat recent MAE bisa naik.

Nah, kalau naik, kita mau ngapain?

Kita butuh lifecycle:

~~~text
observe
↓
detect degradation
↓
new snapshot
↓
retrain
↓
evaluate
↓
register challenger
↓
review
↓
promote
~~~

Itu sudah jauh lebih dari sekadar model.fit().

---

# Analogi: model itu resep, bukan restoran

Kita pakai analogi ini cukup sering karena lumayan membantu.

Bayangin model = recipe.

Recipe bagus belum otomatis bikin restoran jalan.

Restaurant perlu:

| Restaurant | ML System |
| --- | --- |
| Recipe | Model |
| Ingredients | Data |
| Ingredient batch | Dataset snapshot |
| Cooking log | Experiment tracking |
| Approved menu | Model Registry |
| Waiter | API |
| Kitchen schedule | Airflow |
| Standard kitchen environment | Docker |
| Quality dashboard | Monitoring |
| New recipe version | Retraining |

Kenapa analogy ini useful?

Karena sering banget newbie mikir:

> “Kalau model sudah jadi berarti project selesai.”

Padahal sama seperti restaurant:

> “Kalau recipe sudah jadi berarti restaurant selesai.”

Ya nggak juga.

---

# Bedanya ML system dengan software biasa

Traditional software behavior mostly ditentukan oleh code.

Misalnya:

~~~python
def add(a, b):
    return a + b
~~~

Kalau code-nya sama, behavior cukup predictable.

Di ML, behavior model dipengaruhi oleh:

~~~text
code
+
training data
+
features
+
parameters
+
randomness
+
library version
~~~

Misalnya code sama persis, tapi training data beda.

Model output bisa beda.

Artinya source control code saja belum cukup buat explain behavior model.

Ini kenapa MLOps punya concern tambahan seperti:

- dataset lineage,
- experiment tracking,
- model registry,
- model performance monitoring.

---

# Git, DVC, MLflow: bedanya apa?

Ini salah satu confusion paling umum.

Coba lihat seperti ini:

## Git

Pertanyaan:

> “Code version yang dipakai apa?”

Tracks:

- Python,
- YAML,
- docs,
- DAG,
- config.

## DVC

Pertanyaan:

> “Training data snapshot yang dipakai apa?”

Tracks/reproduces:

- data pipeline artifacts,
- snapshot state.

## MLflow

Pertanyaan:

> “Experiment ini menghasilkan apa?”

Tracks:

- parameters,
- metrics,
- model artifact,
- dataset fingerprint,
- run metadata.

Ringkasnya:

~~~text
Git
→ source history

DVC
→ data state

MLflow
→ experiment history
~~~

---

# Airflow masuk di mana?

Airflow beda lagi.

Airflow bukan primarily tracking model.

Airflow jawab:

> “Step mana yang harus jalan dulu?”

Misalnya:

~~~text
release data
↓
validate
↓
aggregate
↓
feature engineering
~~~

Airflow jadi coordinator.

Dia nggak melakukan feature engineering “karena Airflow”.

Dia memanggil Python logic yang kita sudah buat.

Itu distinction yang penting.

---

# Docker masuk di mana?

Docker lebih ke runtime.

Problem-nya:

~~~text
works on my machine
~~~

Kita ingin environment lebih controlled.

Docker bantu package:

~~~text
OS userspace
Python
dependencies
application
startup command
~~~

Jadi application bisa dijalankan lebih consistent across machines.

---

# CI/CD masuk di mana?

CI/CD lebih dekat ke software delivery.

Misalnya ada PR.

Sebelum merge, kita ingin otomatis cek:

~~~text
lint
tests
docs
Docker build
~~~

Itu CI.

Setelah main healthy:

~~~text
build container
↓
publish to registry
~~~

Itu continuous delivery di project kita.

---

# Monitoring kenapa jadi penting?

Karena setelah deployment, kita kehilangan kepastian.

Offline validation bilang:

~~~text
MAE = 10
~~~

Tapi itu berdasarkan historical validation set.

Production-like future data mungkin beda.

Jadi kita nggak bisa bilang:

> “Karena validation bagus maka selamanya bagus.”

Monitoring memberi feedback loop.

---

# Apakah MLOps berarti semua harus otomatis?

Nggak.

Automation itu bukan tujuan akhir.

Contohnya di project kita:

~~~text
retraining
→ otomatis bisa

promotion to champion
→ tetap explicit
~~~

Kenapa?

Karena automation level harus sesuai risk.

Kita tidak ingin model baru langsung mengganti production model hanya karena satu condition terpenuhi tanpa review.

MLOps yang matang bukan berarti “automate everything”.

Lebih tepat:

> **Automate what is repeatable, keep governance where judgment is still important.**

---

# Satu mental model untuk dibawa terus

Kalau nanti tools mulai terasa banyak, balik ke pertanyaan ini:

### Data

~~~text
Where did training data come from?
~~~

### Training

~~~text
What exactly did we run?
~~~

### Registry

~~~text
Which model is approved?
~~~

### Serving

~~~text
How does application use it?
~~~

### Monitoring

~~~text
Is system healthy and is model still good?
~~~

### Retraining

~~~text
What do we do when quality drops?
~~~

Kalau kalian bisa follow six questions ini, kalian sudah punya kerangka berpikir MLOps yang jauh lebih useful daripada sekadar hafal tools.
