# Docker Compose — Menyalakan Satu MLOps Stack Tanpa Buka Lima Terminal Manual

Setelah Docker section, kita sudah ngerti satu image bisa dijalankan jadi container.

Sekarang problem berikutnya:

Project kita bukan satu service.

Kita punya:

~~~text
MLflow
Airflow
FastAPI
Prometheus
Grafana
~~~

Kalau semuanya start manual, kita harus ingat:

- command,
- port,
- network,
- environment variable,
- storage,
- startup order.

Docker Compose masuk buat define **multi-service local environment**.

---

## Analogi: satu kompleks gedung

Docker image seperti blueprint unit.

Container seperti unit yang sedang dipakai.

Docker Compose seperti site plan satu kompleks:

> Ada service apa saja? Mereka tinggal di network mana? Port apa yang dibuka? Storage mana yang dipakai? Service mana nunggu service lain?

Semua didefinisikan di:

~~~text
docker-compose.yml
~~~

---

## Start stack

~~~bash
docker compose up -d --build
~~~

Kita bedah:

### up

Create/start service.

### -d

Detached mode.

Terminal kalian balik, container tetap jalan.

### --build

Build local images dulu kalau perlu.

---

## Service kita

### MLflow

~~~text
host:
localhost:5000

internal Compose:
mlflow:5000
~~~

Responsibility:

- tracking server,
- registry,
- artifact access.

### FastAPI

~~~text
localhost:8000
~~~

Serve champion prediction.

### Airflow

~~~text
localhost:8080
~~~

Orchestrate data/training/monitoring workflow.

### Prometheus

~~~text
localhost:9090
~~~

Scrape metrics.

### Grafana

~~~text
localhost:3000
~~~

Visualize metrics.

---

## Kenapa internal hostname beda?

Ini penting banget.

Dari browser laptop:

~~~text
http://localhost:5000
~~~

Dari API container:

~~~text
http://mlflow:5000
~~~

Kalau API container call localhost:5000, dia cari MLflow **di dalam dirinya sendiri**.

Compose DNS kasih nama service.

Makanya:

~~~text
api → mlflow
prometheus → api
grafana → prometheus
~~~

---

## depends_on

Kadang service A butuh B.

API butuh MLflow.

Tapi container process started bukan berarti service ready menerima request.

Makanya MLflow punya healthcheck.

Compose bisa wait sampai health condition.

Mental model:

~~~text
container running
≠
application ready
~~~

Ini subtle tapi real operational concern.

---

## Healthcheck

Healthcheck adalah test readiness/liveness sederhana.

Misalnya request HTTP ke service.

Kalau belum healthy, dependent service bisa ditahan.

Ini mengurangi race condition startup.

---

## Shared data folder

Kita bind mount:

~~~text
./data
→ /app/data
~~~

Benefit workshop:

- Airflow container bisa write,
- API container bisa read,
- host bisa inspect file yang sama.

Jadi local data acts as shared simple storage.

Production mungkin pakai object storage/database instead.

---

## Shared MLflow state

Audit workshop menemukan issue penting.

Kalau local MLflow pakai state A, lalu Docker MLflow pakai state B, participant bakal mengalami:

> “Lho champion yang tadi saya register kok hilang?”

Makanya local helper dan Docker MLflow share:

~~~text
.mlflow/
~~~

Ini bikin transition:

~~~text
local MLflow
→ Docker MLflow
~~~

tetap continuity.

---

## Named volumes

Kita punya named volume untuk service state seperti:

~~~text
airflow-home
prometheus-data
grafana-data
dvc-cache
~~~

Kenapa volume?

Container disposable.

Kalau container delete, state jangan selalu ikut hilang.

Volume separate lifecycle storage dari container process.

---

## down vs down -v

~~~bash
docker compose down
~~~

Stop/remove containers/network, keep named volumes.

~~~bash
docker compose down -v
~~~

Juga remove named volumes.

Jadi command kedua destructive untuk local service state.

Tapi bind-mounted .mlflow folder tidak otomatis hilang karena bukan named volume itu.

---

## Workspace service

Kita punya workspace profile untuk command one-shot.

Contoh:

~~~bash
docker compose run --rm workspace python scripts/doctor.py
~~~

Kenapa nggak workspace jalan terus?

Karena dia bukan service.

Dia cuma environment buat execute project command.

Setelah command selesai, container remove.

---

## Profiles

Compose profile bisa hide optional service dari default startup.

Workspace pakai profile karena tidak perlu hidup terus.

Ini pattern useful kalau stack punya debug/admin tools.

---

## Logs

Semua:

~~~bash
docker compose logs -f
~~~

Specific:

~~~bash
docker compose logs -f api
~~~

Logs adalah first stop debugging runtime.

Kalau API container crash, jangan langsung edit model.

Baca log dulu.

---

## Common mistakes

### Port conflict

Local MLflow masih running.

Compose mau bind 5000.

Error.

Stop local process dulu.

### Salah hostname

Container call localhost untuk service lain.

Connection refused.

### Data tidak muncul

Bind mount path berbeda atau permission problem.

### Reset state tanpa sadar

Run down -v lalu Airflow/Grafana state hilang.

---

## Compose bukan Kubernetes mini

Compose bagus banget untuk local multi-service development.

Tapi dia bukan distributed production orchestrator.

Jangan pakai workshop Compose architecture untuk conclude “production deployment selesai”.

Yang kita pelajari adalah:

- service boundaries,
- networking,
- storage,
- config,
- health dependency.

---

## Checkpoint

1. Docker Compose solve problem apa?
2. Kenapa mlflow:5000 dipakai antar container?
3. Healthcheck beda apa dengan container process running?
4. Bind mount dan named volume beda apa?
5. down -v efeknya apa?
6. Workspace service kenapa one-shot?
