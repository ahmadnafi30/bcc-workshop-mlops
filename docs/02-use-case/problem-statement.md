# Problem Statement

Di workshop ini kita bakal bikin **Taxi Demand Forecasting** untuk NYC Yellow Taxi.

Fokus kita bukan bikin model yang paling fancy atau ngejar leaderboard. Yang mau kita pelajari adalah gimana sebuah model ML bisa hidup dari awal sampai production: data masuk, diproses, ditrain, ditrack, diserve, dimonitor, lalu diretrain kalau performanya mulai turun.

## The problem

Bayangin kita punya sistem yang harus jawab pertanyaan ini:

> Di setiap taxi zone di Manhattan, kira-kira bakal ada berapa pickup dalam satu jam ke depan?

Contohnya:

```text
Zone: Midtown Center

14:00 -> 128 pickups
15:00 -> 141 pickups
16:00 -> 153 pickups
17:00 -> 169 pickups

Prediction for 18:00 -> 182 pickups
```

Kalau demand satu jam ke depan bisa diprediksi, secara business ini bisa dipakai untuk planning supply, repositioning, capacity planning, atau sekadar understanding demand pattern.

Di workshop ini kita tidak akan bikin optimization system setelah prediksi. Scope kita berhenti di **forecasting + MLOps lifecycle**.

## Prediction unit

Satu prediction bukan untuk satu individual trip.

Prediction kita adalah:

```text
1 taxi zone x 1 target hour = predicted number of pickups
```

Jadi model akan melihat historical demand suatu zone dan menjawab demand pada jam berikutnya.

## Scope

- Service: **NYC Yellow Taxi**
- Area: **Manhattan pickup zones**
- Time granularity: **hourly**
- Forecast horizon: **1 hour ahead**
- Data period: **January - March 2025**
- Main data source: **NYC TLC Trip Record Data**
- Primary metric: **MAE**
- Secondary metric: **RMSE**

Kenapa Manhattan saja? Karena kita nggak butuh seluruh NYC buat memahami lifecycle MLOps. Yellow Taxi activity di Manhattan juga cukup padat untuk bikin demand pattern yang interesting.

## What are we actually learning?

Secara ML, problem ini sebenarnya cukup straightforward. Yang bikin project ini menarik justru lifecycle-nya:

```text
Trip data
   ↓
Batch ingestion
   ↓
Preprocessing
   ↓
Feature engineering
   ↓
Training
   ↓
Experiment tracking
   ↓
Model registry
   ↓
Serving
   ↓
Monitoring
   ↓
Retraining
```

Tools yang kita pakai masuk karena ada problem yang memang perlu diselesaikan, bukan karena sekadar pengen pakai banyak tools.

| Problem | Tool / Concept |
| --- | --- |
| Data datang per batch dan workflow harus berurutan | Airflow |
| Training dataset perlu reproducible | DVC |
| Experiment mulai banyak dan susah dibandingin | MLflow |
| Model perlu diakses aplikasi lain | FastAPI |
| Environment harus konsisten | Docker |
| Testing dan delivery jangan manual terus | GitHub Actions |
| Service production perlu dipantau | Prometheus + Grafana |

## What does production mean here?

Kita nggak punya taxi system live beneran, jadi kita pakai **historical replay**.

Data January-March 2025 sebenarnya sudah tersedia dari awal, tapi pipeline dibuat seolah-olah data itu datang sedikit demi sedikit setiap hari.

```text
DAG run 1 -> release data Jan 27
DAG run 2 -> release data Jan 28
DAG run 3 -> release data Jan 29
...
```

Dari sisi pipeline, behavior-nya jadi mirip production batch system: setiap run cuma melihat data yang memang sudah available pada waktu itu.

Detail mekanismenya ada di [Historical Replay](historical-replay.md).

## Success criteria

Di akhir project, system kita minimal bisa:

1. menerima batch taxi trip baru,
2. mengubah raw trip menjadi hourly demand per zone,
3. menghasilkan feature tanpa data leakage,
4. train dan evaluate model,
5. log experiment ke MLflow,
6. register model yang layak,
7. serve prediction lewat API,
8. package service menggunakan Docker,
9. menjalankan CI/CD,
10. monitor service dan recent model performance,
11. trigger retraining ketika memang dibutuhkan.

Kalau semua ini jalan, kita sudah punya mini end-to-end MLOps system yang cukup representative buat workshop.