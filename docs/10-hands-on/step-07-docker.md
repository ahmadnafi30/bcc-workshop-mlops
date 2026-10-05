# Step 7 — Docker Compose: Running the MLOps Stack Together

Sekarang kita sudah pernah menjalankan:

- MLflow,
- Airflow,
- FastAPI,

sebagai local process.

Kalau workshop berhenti di situ sebenarnya sudah bisa.

Tapi sekarang kita mau bikin local environment lebih standardized.

Masuk Docker + Compose.

---

# Sebelum start Compose

Stop local service yang pakai port sama.

Ctrl+C terminal:

- MLflow,
- FastAPI,
- Airflow.

Kenapa?

Karena Compose mau pakai:

~~~text
5000
8000
8080
~~~

Kalau local process masih pegang port:

~~~text
address already in use
~~~

---

# 1. Check Docker

~~~bash
docker --version
docker compose version
~~~

Kalau error, selesaikan Docker setup dulu.

---

# 2. Build and start stack

~~~bash
docker compose up -d --build
~~~

First build bisa lama.

Airflow dependency particularly heavy.

Jangan kira hang hanya karena beberapa menit.

---

# 3. Check status

~~~bash
docker compose ps
~~~

Kalian harus lihat service:

~~~text
mlflow
api
airflow
prometheus
grafana
~~~

Perhatikan status health kalau available.

---

# 4. Open all interfaces

## MLflow

~~~text
http://localhost:5000
~~~

## FastAPI

~~~text
http://localhost:8000/docs
~~~

## Airflow

~~~text
http://localhost:8080
~~~

## Prometheus

~~~text
http://localhost:9090
~~~

## Grafana

~~~text
http://localhost:3000
~~~

Sekarang satu command menyalakan whole stack.

---

# 5. Check MLflow continuity

Buka MLflow.

Champion dari step sebelumnya harus masih ada.

Kenapa?

Karena local helper dan Docker MLflow share:

~~~text
.mlflow/
~~~

Kalau hilang, berarti state path salah / run sebelumnya pakai tracking store lain.

---

# 6. Open API /model-info

~~~text
http://localhost:8000/model-info
~~~

API container sekarang reach MLflow container via:

~~~text
http://mlflow:5000
~~~

Bukan localhost.

---

# 7. Understand network perspective

Ini mini exercise.

From browser laptop:

~~~text
localhost:5000
~~~

From API container:

~~~text
mlflow:5000
~~~

Same logical service.

Different network location.

Kalau kalian paham ini, Docker networking suddenly jauh lebih masuk akal.

---

# 8. Inspect logs

API:

~~~bash
docker compose logs -f api
~~~

MLflow:

~~~bash
docker compose logs -f mlflow
~~~

Airflow:

~~~bash
docker compose logs -f airflow
~~~

Ctrl+C hanya stop log follow, bukan container.

---

# 9. Run workspace one-shot

~~~bash
docker compose run --rm workspace   python scripts/doctor.py
~~~

Workspace container berguna buat menjalankan project command di containerized core environment.

---

# 10. Inspect mounted data

Kalau Airflow inside container create file:

~~~text
/app/data/processed/...
~~~

host juga melihat:

~~~text
./data/processed/...
~~~

karena bind mount.

Ini yang bikin API dan Airflow share same data state.

---

# 11. Stop stack

~~~bash
docker compose down
~~~

Run:

~~~bash
docker compose ps
~~~

Long-running service harus berhenti.

---

# 12. Start lagi

~~~bash
docker compose up -d
~~~

Named volume state masih ada.

---

# 13. Apa yang terjadi kalau down -v?

~~~bash
docker compose down -v
~~~

Named volumes dihapus.

Jangan lakukan kalau nggak ingin reset:

- Airflow state,
- Prometheus time series,
- Grafana local state.

.mlflow bind mount tetap di host kecuali dihapus manual.

---

# Mini challenge

Pertanyaan:

> Kenapa API container nggak connect ke localhost:5000 untuk MLflow?

Jawaban:

> Karena localhost di API container menunjuk API container itself, bukan MLflow container.

---

# Common issues

## Port already in use

Local process belum stop.

## API unhealthy

Check:

~~~bash
docker compose logs api
~~~

## API model-info 503

MLflow healthy tapi champion missing atau Registry state tidak available.

## Build very slow

First build normal.

Cache membantu subsequent build.

---

# Checkpoint

Kalian harus bisa explain:

~~~text
image
container
service
bind mount
named volume
internal service name
published port
~~~

Next kita pindah dari local runtime ke GitHub automation.
