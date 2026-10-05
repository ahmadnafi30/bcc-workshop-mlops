# Step 7 — Docker: Bawa Semua Service ke Environment yang Lebih Konsisten

Sekarang local flow jalan.

Tapi workshop real punya laptop berbeda.

Kita ingin reduce:

> “Di laptop saya works.”

masalah.

Sekarang kita pindah dari local processes ke container stack.

---

## Goal

Setelah step ini:

- Docker images build,
- Compose services up,
- local MLflow state tetap ada,
- API bisa resolve champion dari Docker MLflow,
- kalian ngerti networking dan volumes.

---

## 0. Stop local processes dulu

Stop:

- MLflow local,
- FastAPI local,
- Airflow local.

Ctrl+C.

Kenapa?

Karena Compose mau bind port sama.

Kalau local MLflow masih pakai 5000:

~~~text
port already in use
~~~

---

## 1. Build + start

~~~bash
docker compose up -d --build
~~~

First build bisa lama.

Airflow particularly heavy.

Jangan cancel cuma karena beberapa menit.

---

## 2. Check status

~~~bash
docker compose ps
~~~

Look for:

~~~text
mlflow
api
airflow
prometheus
grafana
~~~

Status healthy/running.

---

## 3. Open MLflow

~~~text
http://localhost:5000
~~~

Pertanyaan penting:

> “Experiment dan champion tadi masih ada nggak?”

Harusnya ada.

Kenapa?

Local helper dan Compose share:

~~~text
.mlflow/
~~~

Ini continuity fix yang sengaja dibuat.

---

## 4. Open API model-info

~~~text
http://localhost:8000/model-info
~~~

Kalau champion metadata keluar, berarti:

~~~text
API container
↓
network
↓
MLflow container
↓
shared registry state
~~~

working.

---

## 5. Network exercise

Dari browser:

~~~text
localhost:5000
~~~

Tapi environment variable API:

~~~text
http://mlflow:5000
~~~

Coba explain kenapa beda.

Kalau kalian jawab:

> “Karena localhost di container refer ke container itu sendiri.”

correct.

---

## 6. Inspect logs

~~~bash
docker compose logs -f api
~~~

Send prediction dari Swagger.

Lihat logs.

Stop log follow dengan Ctrl+C.

Container tetap hidup.

---

## 7. Inspect volumes conceptually

Run:

~~~bash
docker volume ls
~~~

Kalian mungkin lihat Compose volumes.

Pertanyaan:

> “Kenapa .mlflow nggak muncul sebagai named volume?”

Karena .mlflow adalah bind mount host folder.

---

## 8. Workspace

~~~bash
docker compose run --rm workspace python scripts/doctor.py
~~~

Ini create temporary workspace container.

Command selesai → container remove.

Useful buat one-off task.

---

## 9. Restart service

Coba:

~~~bash
docker compose restart api
~~~

Apakah MLflow state hilang?

No.

Service process lifecycle beda dari persistent storage.

---

## 10. Stop stack

~~~bash
docker compose down
~~~

Start lagi:

~~~bash
docker compose up -d
~~~

Named volumes tetap.

---

## Mini challenge

Apa bedanya:

~~~bash
docker compose down
~~~

dengan:

~~~bash
docker compose down -v
~~~

Jawaban:

-v remove named volumes juga.

Jangan run destructive command tanpa ngerti state apa yang hilang.

---

## Checkpoint

1. Image vs container?
2. Host port vs container port?
3. localhost vs service name?
4. Bind mount vs named volume?
5. Kenapa MLflow state survive?
6. Kenapa service restart tidak otomatis delete data?
