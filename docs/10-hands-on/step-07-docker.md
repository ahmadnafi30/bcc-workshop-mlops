# Step 7 — Docker: Dari Local Processes Jadi Multi-Service Stack yang Reproducible

Sebelum step ini kalian mungkin punya beberapa terminal:

~~~text
MLflow
FastAPI
Airflow
~~~

Kalau tambah Prometheus/Grafana manual, makin ramai.

Sekarang kita package runtime dan jalankan stack via Docker Compose.

Goal bukan sekadar berhasil docker compose up.

Kita ingin ngerti image, container, network, volume, health, dan state continuity.

---

## Goal

Setelah selesai kalian bisa explain:

- image vs container;
- Dockerfile target;
- build vs run;
- host port vs container port;
- localhost trap;
- bind mount vs volume;
- shared .mlflow state;
- healthcheck;
- Compose service dependency;
- logs/ps/down lifecycle.

---

# 1. Check Docker

~~~bash
docker --version
docker compose version
~~~

Kalau command missing, bereskan Docker dulu.

Windows user biasanya lebih nyaman lewat WSL2 + Docker integration.

---

# 2. Stop local processes dulu

Kalau local Uvicorn masih pakai 8000, MLflow 5000, Airflow 8080:

Compose akan conflict port.

Stop dengan Ctrl+C.

Question:

> “Apakah stop local MLflow menghapus Registry?”

No.

State ada di .mlflow folder.

---

# 3. Inspect Dockerfile

Open:

~~~text
docker/Dockerfile
~~~

Cari targets:

~~~text
base
api
mlflow
airflow
~~~

Kenapa satu Dockerfile banyak target?

Shared base environment, different service runtime.

---

# 4. Build one target manually — optional

~~~bash
docker build -f docker/Dockerfile --target api -t bcc-mlops-api .
~~~

Ini membantu understand:

~~~text
Dockerfile
↓
build
↓
image
~~~

Check:

~~~bash
docker images | grep bcc
~~~

---

# 5. Image vs container

Image:

> built template.

Container:

> running instance.

Kalau build selesai tapi belum run, service belum hidup.

Kalau container stop, image masih ada.

Lifecycle berbeda.

---

# 6. Start full stack

~~~bash
docker compose up -d --build
~~~

First run bisa lama.

Airflow dependencies heavy.

Jangan interrupt hanya karena beberapa menit.

---

# 7. docker compose ps

~~~bash
docker compose ps
~~~

Lihat:

- service;
- status;
- health;
- ports.

Expected services:

~~~text
mlflow
api
airflow
prometheus
grafana
~~~

Workspace tidak long-running by default.

---

# 8. Open all service URLs

| Service | URL |
| --- | --- |
| MLflow | http://localhost:5000 |
| Airflow | http://localhost:8080 |
| FastAPI | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

Jangan langsung assume all ready kalau browser error pertama detik startup.

Healthchecks/startup bisa perlu waktu.

---

# 9. Verify MLflow state continuity

Open MLflow.

Champion yang dibuat di Step 4 harus tetap ada.

Kalau ada, shared state works.

Kenapa?

Local helper dan Docker service sama-sama use:

~~~text
.mlflow/
~~~

---

# 10. Kalau champion hilang, apa yang dicek?

Jangan retrain dulu.

Check:

- local MLflow dulu pakai start_mlflow.py?
- .mlflow folder ada?
- Compose mount benar?
- current working directory benar?
- permission?

Likely state-path issue, bukan model issue.

---

# 11. Test FastAPI inside Compose

~~~bash
curl http://localhost:8000/health
curl http://localhost:8000/model-info
~~~

Kalau health works tapi model-info fail, same dependency reasoning berlaku.

---

# 12. Host URL vs service URL

Browser:

~~~text
localhost:5000
~~~

API container:

~~~text
http://mlflow:5000
~~~

Kenapa bukan localhost?

Karena localhost di API container adalah API container sendiri.

Compose DNS resolve service name.

---

# 13. Port mapping thought experiment

Compose:

~~~text
8000:8000
~~~

Kiri host.

Kanan container.

Kalau change host to:

~~~text
9000:8000
~~~

browser access:

~~~text
localhost:9000
~~~

container internal app tetap listen 8000.

This distinction useful.

---

# 14. Shared data bind mount

Compose mount project data folder.

Kenapa?

Airflow writes:

~~~text
data/processed/...
~~~

FastAPI reads same history.

Host participant juga inspect same files.

One simple shared filesystem for local workshop.

---

# 15. Named volumes

Prometheus/Grafana/Airflow punya persistent service state.

Named volume survive container recreation.

Container disposable.

Data state can persist.

---

# 16. Check logs

~~~bash
docker compose logs -f api
~~~

Try MLflow:

Lihat logs.

Stop follow dengan Ctrl+C.

Container tetap running.

---

# 17. Logs bukan same as metrics

Logs:

~~~text
detailed event/error
~~~

Metrics:

~~~text
aggregated numeric trend
~~~

Nanti dua-duanya useful.

Jangan berharap Grafana menggantikan stack traces.

---

# 18. Healthcheck

Container status bisa:

~~~text
running
~~~

tapi health:

~~~text
starting
~~~

Application belum ready.

Compose depends_on health behavior membantu startup ordering.

---

# 19. Workspace one-shot container

Run:

~~~bash
docker compose run --rm workspace python scripts/doctor.py
~~~

Ini start temporary workspace container.

Command selesai → container removed.

Why useful?

Kita bisa run project tool dalam same containerized environment tanpa install local extra tool.

---

# 20. Container inspect vs source changes

Kalau code copied into image lalu source host berubah, running container tidak otomatis update unless bind-mounted source or rebuild.

Project production-like services use built image behavior.

So after source change:

~~~bash
docker compose up -d --build
~~~

may be needed.

---

# 21. docker compose down

~~~bash
docker compose down
~~~

Stops/removes containers + network.

Named volumes remain.

---

# 22. docker compose down -v

~~~bash
docker compose down -v
~~~

Also removes named volumes.

Use carefully.

Prometheus/Grafana/Airflow state reset.

Shared .mlflow bind folder remains because it is host path.

---

# 23. Full reset vs normal restart

Normal:

~~~bash
docker compose down
docker compose up -d
~~~

keeps volumes.

Full reset:

~~~bash
docker compose down -v
~~~

destructive.

Jangan gunakan full reset sebagai first debugging instinct.

Bisa menghapus evidence/state yang sebenarnya useful.

---

# 24. Scenario: API cannot connect MLflow

Error:

~~~text
connection refused localhost:5000
~~~

Inside API container, likely wrong hostname.

Correct internal:

~~~text
mlflow:5000
~~~

This is classic container networking bug.

---

# 25. Scenario: port already allocated

Compose error host port 8000 used.

Check local process.

Linux:

~~~bash
ss -ltnp | grep 8000
~~~

or stop previous Uvicorn.

Problem host binding, bukan Dockerfile necessarily.

---

# 26. Scenario: Prometheus starts before API healthy?

depends_on + healthcheck design helps.

Still, always inspect target page after stack ready.

Distributed services have startup timing.

---

# 27. Why not install everything one container?

Because service lifecycle different.

If Grafana restart, API shouldn't necessarily restart.

If API scale 3 replicas, MLflow need not scale same.

Separation creates flexibility.

---

# 28. Docker image as delivery artifact

Step 8 GitHub Actions later build same service targets and push to GHCR.

So local Docker learning directly connects CI/CD.

~~~text
Dockerfile
↓
local build
↓
CI build
↓
registry image
~~~

One artifact definition across lifecycle.

---

# 29. Checkpoint

1. Image vs container?
2. Build vs run?
3. Kenapa local process harus stop sebelum Compose?
4. Host localhost vs container service name?
5. Apa arti 9000:8000?
6. Bind mount vs named volume?
7. Kenapa .mlflow shared?
8. Running vs healthy?
9. Workspace service buat apa?
10. Source change kapan perlu rebuild?
11. down vs down -v?
12. Port conflict debug di layer mana?
13. Kenapa service dipisah container?
14. Docker image connect ke CI/CD bagaimana?

Kalau clear, next kita lihat bagaimana GitHub otomatis verify dan publish image tersebut.
