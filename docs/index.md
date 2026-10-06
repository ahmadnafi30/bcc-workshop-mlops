# Hi peers, welcome to BCC Workshop — MLOps 👋

Welcome peers! Di workshop ini kita bakal belajar **MLOps dari awal sampai punya satu lifecycle yang utuh**, tapi tenang aja, kita nggak akan mulai dari definisi yang terlalu textbook atau langsung dilempar ke banyak tools.

Workshop ini dibawakan oleh:

- **Ahmad Nafi Mubarok**
- **Fatoni Murfid Syafii**

Baru pertama kali belajar? Mulai dari [Mulai di Sini — Start Here](00-start-here.md) untuk peta belajar dan tour UI tools.

Untuk mengikuti satu modul yang utuh, buka [Modul Workshop](workshop-module.md).
Modul memuat agenda, konsep, praktik, checkpoint, tugas, dan panduan fasilitator.
Untuk menjalankan demo monitoring terlebih dahulu, gunakan
[Quickstart Grafana](10-hands-on/dashboard-quickstart.md).

Kalau sekarang kalian masih bingung bedanya **MLflow, Airflow, DVC, Docker, CI/CD, Prometheus, Grafana**, itu sangat normal. Bahkan salah satu tujuan utama workshop ini justru supaya setelah selesai kalian nggak cuma tahu nama tools-nya, tapi ngerti:

> “Oh, tool ini masuk karena sebelumnya kita punya problem ini.”

Itu penting banget, karena MLOps gampang sekali kelihatan seperti kumpulan tools random kalau kita belajar dari sisi tools dulu.

---

## Sebelum mulai, coba bayangin skenario ini

Kalian seorang Data Scientist. Kalian punya notebook, data sudah bersih, model sudah ditrain, dan hasilnya lumayan bagus.

Misalnya:

~~~text
Validation MAE = 10.3
~~~

Kalian senang. Model disimpan:

~~~text
model.pkl
~~~

Lalu kalian bilang:

> “Done nih, modelnya sudah jadi.”

Untuk tugas kuliah atau eksperimen pribadi, mungkin memang sudah cukup.

Tapi beberapa hari kemudian ada pertanyaan:

> “Model ini pakai dataset yang mana?”

Kalian jawab:

> “Kayaknya dataset final_v2.csv.”

Terus ditanya lagi:

> “Hyperparameter yang dipakai apa?”

Mulai bingung.

Terus ada pertanyaan berikutnya:

> “Model ini bisa dipakai application lain nggak?”

> “Kalau besok ada data baru siapa yang jalanin training lagi?”

> “Kalau model yang baru malah lebih jelek gimana?”

> “Kalau API-nya hidup tapi modelnya makin ngawur, kita tahu dari mana?”

Nah... mulai dari sini problem-nya sudah bukan cuma **Machine Learning**.

Kita mulai masuk ke:

~~~text
How do we operate machine learning systems?
~~~

Dan kurang lebih itulah area yang kita bahas sebagai **MLOps**.

---

# Use case kita

Biar semua tools yang kita pelajari punya cerita yang nyambung, workshop ini pakai satu use case dari awal sampai akhir:

> **Predicting NYC Yellow Taxi demand one hour ahead for each Manhattan taxi zone.**

Secara sederhana, kita mau menjawab:

> “Untuk jam berikutnya, di area ini kira-kira bakal ada berapa pickup taxi?”

Contohnya:

~~~text
Sekarang: 17:00

Target:
Zone 161
18:00

Prediction:
147.8 pickups
~~~

Kenapa use case ini menarik?

Karena kita punya beberapa hal yang memang cocok banget buat MLOps:

- data datang berdasarkan waktu,
- model pakai historical behavior,
- ground truth baru tersedia setelah target time lewat,
- model bisa memburuk seiring waktu,
- prediction bisa diserve lewat API,
- retraining bisa dilakukan saat performa turun.

Jadi kita nggak perlu mengarang-ngarang alasan kenapa monitoring atau retraining dibutuhkan.

---

# Dari satu file model sampai full lifecycle

Awalnya mungkin project kita cuma begini:

~~~text
dataset
   ↓
train.py
   ↓
model.joblib
~~~

Tapi selama workshop, lifecycle-nya berkembang jadi:

~~~text
NYC TLC Data
     ↓
Data Preparation
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
Docker
     ↓
CI/CD
     ↓
Prometheus
     ↓
Grafana
     ↓
Model Performance Monitoring
     ↓
Retraining
     ↓
Challenger Model
     ↓
Review / Promotion
     ↓
Champion
~~~

Kelihatannya panjang? Iya.

Tapi jangan coba dihafal dari sekarang.

Kita bakal build satu per satu dan setiap step selalu dimulai dari pertanyaan:

> **“Sekarang problem kita apa?”**

Kalau problem-nya sudah terasa, biasanya tool berikutnya jadi jauh lebih gampang dipahami.

---

# Satu analogi yang bakal sering kita pakai

Coba anggap **model Machine Learning itu recipe**.

Recipe bisa bagus banget. Tapi recipe doang belum jadi restoran.

Restoran masih butuh:

- ingredients,
- supplier,
- kitchen,
- cooking process,
- quality control,
- waiter,
- monitoring,
- inventory,
- dan cara update menu.

Kurang lebih:

| Restaurant | ML System |
| --- | --- |
| Recipe | Model |
| Ingredients | Data |
| Batch ingredients | Dataset version |
| Cooking process | Training pipeline |
| Experiment notes | MLflow Tracking |
| Approved menu | Model Registry |
| Waiter | FastAPI |
| Kitchen environment | Docker |
| Daily schedule | Airflow |
| Control room | Prometheus + Grafana |
| Update recipe | Retraining |

Jadi kalau nanti kalian merasa:

> “Kok tool-nya banyak?”

Coba balik ke analogi itu.

Karena yang kita bangun bukan hanya model. Kita bangun **system around the model**.

---

# Apa yang perlu kalian kuasai sebelum workshop?

Kalian nggak harus sudah pernah pakai tools MLOps.

Yang penting cukup nyaman dengan:

- Python dasar,
- Pandas basic,
- konsep training dan validation,
- regression secara umum,
- sedikit Git.

Kalau istilah seperti DAG, container, model registry, artifact, XCom, metrics scraping masih asing, justru docs ini dibuat untuk itu.

---

# Cara pakai dokumentasi ini

Docs ini sengaja dibuat agak panjang.

Bukan karena semuanya harus dihafal, tapi supaya setelah workshop kalian bisa balik lagi dan baca sebagai reference.

Ada dua cara pakai:

### Kalau lagi ikut live workshop

Ikutin bagian **Hands-on Workshop** secara urut.

~~~text
Step 0
Setup

Step 1
Data

Step 2
Baseline Model

Step 3
DVC

Step 4
MLflow

Step 5
Airflow

Step 6
FastAPI

Step 7
Docker

Step 8
CI/CD

Step 9
Monitoring

Step 10
Retraining
~~~

### Kalau lagi belajar sendiri

Mulai dari:

1. Workshop Overview
2. MLOps from Zero
3. Architecture
4. Use Case
5. Baru masuk tools satu per satu

---

# Mindset utama workshop ini

Ada satu kalimat yang menurut kami paling penting:

> **Jangan mulai dari tool. Mulai dari problem.**

Kita nggak pakai Airflow karena “MLOps biasanya pakai Airflow”.

Kita pakai Airflow karena:

> “Manual pipeline kita mulai susah dikoordinasikan.”

Kita nggak pakai MLflow karena kelihatan keren.

Kita pakai MLflow karena:

> “Eksperimen kita mulai susah dilacak.”

Kita nggak pakai Prometheus karena architecture diagram terasa kurang penuh.

Kita pakai Prometheus karena:

> “Setelah model diserve, kita perlu tahu system-nya masih sehat atau nggak.”

Kalau mindset ini kebawa setelah workshop, kalian sebenarnya sudah dapat bagian paling pentingnya.

Next, kita mulai dari **MLOps from Zero**: sebenarnya MLOps itu apa sih, dan kenapa Machine Learning project punya problem yang sedikit berbeda dari software biasa?
