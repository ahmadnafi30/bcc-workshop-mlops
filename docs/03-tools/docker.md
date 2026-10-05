# Docker — Kenapa Works on My Machine Itu Nggak Cukup?

Sampai titik ini, project kita bisa jalan di local Python environment.

Terus masalah klasik muncul:

> “Di laptopku jalan kok.”

Teman kalian clone repo.

Run.

Boom:

~~~text
ModuleNotFoundError
wrong Python version
missing package
different system library
~~~

Nah, Docker masuk bukan karena keren di architecture diagram, tapi karena kita butuh **runtime consistency**.

---

## Analogi: shipping container

Sebelum standard shipping container, cargo beda-beda butuh handling beda.

Container bikin bentuk luar standardized.

Docker kurang lebih melakukan hal yang sama untuk application runtime.

~~~text
application code
+
runtime dependencies
+
environment setup
+
startup command
↓
image
~~~

Image ini bisa dijalankan jadi container.

---

## Image vs Container

Ini basic tapi penting banget.

### Image

Blueprint.

Read-only-ish template hasil build.

### Container

Running instance dari image.

Analogi programming:

~~~text
class
→ image

object
→ container
~~~

Nggak 100% technically equivalent, tapi intuition-nya membantu.

Satu image bisa dijalankan jadi beberapa container.

---

## Dockerfile itu apa?

Dockerfile = recipe buat build image.

Project kita punya:

~~~text
docker/Dockerfile
~~~

Instruction umum:

~~~text
FROM
RUN
COPY
ENV
WORKDIR
CMD
~~~

### FROM

Base environment.

Misalnya Python 3.11 slim.

### RUN

Command saat image build.

Contoh install dependency.

### COPY

Copy file dari build context ke image.

### WORKDIR

Working directory.

### ENV

Environment variable.

### CMD

Default command saat container start.

---

## Build time vs run time

Ini sering bikin bingung.

### Build time

Saat:

~~~bash
docker build
~~~

Docker execute Dockerfile steps dan produce image.

### Run time

Saat:

~~~bash
docker run
~~~

atau:

~~~bash
docker compose up
~~~

Container start dari image.

Kalau code di-copy ke image saat build dan code host berubah, container lama nggak otomatis tahu. Biasanya perlu rebuild.

---

## Multi-stage / multi-target project kita

Satu Dockerfile dipakai untuk beberapa target:

~~~text
base
├── api
├── mlflow
└── airflow
~~~

Kenapa?

Karena ketiga service share core project environment, tapi startup dan dependency tambahan berbeda.

### base

Punya:

- Python,
- uv,
- project package,
- core dependency.

### api

Start:

~~~text
uvicorn api.main:app
~~~

### mlflow

Start MLflow tracking server.

### airflow

Install Airflow dependency group dan start Airflow.

---

## Kenapa nggak satu container isi semuanya?

Technically bisa.

Satu container:

~~~text
FastAPI
MLflow
Airflow
Prometheus
Grafana
~~~

Tapi boundary service jadi blur.

Kalau MLflow restart, kenapa API harus ikut restart?

Kalau Grafana error, kenapa training service terpengaruh?

Separation bikin lifecycle lebih clear.

~~~text
API
→ serve prediction

MLflow
→ track/model registry

Airflow
→ orchestration
~~~

Service responsibility berbeda.

---

## Layer cache

Docker build punya layer.

Misalnya dependency installation adalah layer yang mahal.

Kalau dependency metadata nggak berubah, Docker bisa reuse cache.

Makanya Dockerfile sering copy dependency metadata dulu, install dependency, baru copy code yang lebih sering berubah.

Intuition:

> “Jangan ulang kerja mahal kalau input step itu nggak berubah.”

Ini mirip caching concept secara umum.

---

## Bind mount vs named volume

Project kita pakai keduanya.

### Bind mount

Host path langsung di-mount.

Contoh:

~~~text
./data
→ /app/data
~~~

Kalau Airflow generate file di container, kita bisa lihat dari host.

Useful buat workshop.

### Named volume

Docker manage storage.

Contoh:

~~~text
airflow-home
prometheus-data
grafana-data
~~~

Kita nggak perlu peduli physical host path-nya.

---

## Networking — localhost trap

Ini salah satu error paling common.

Dari laptop host:

~~~text
http://localhost:5000
~~~

buat akses MLflow.

Tapi dari API container:

~~~text
http://mlflow:5000
~~~

Kenapa?

Karena di dalam API container:

~~~text
localhost
=
API container itu sendiri
~~~

MLflow ada di container lain.

Docker Compose kasih hostname service:

~~~text
mlflow
api
airflow
prometheus
grafana
~~~

Jadi service-to-service communication pakai service name.

---

## Port mapping

Misalnya:

~~~text
5000:5000
~~~

Artinya:

~~~text
host port 5000
→ container port 5000
~~~

Browser host akses host port.

Container lain biasanya nggak perlu lewat published host port. Dia bisa langsung pakai internal service port.

---

## Environment variable

Kenapa connection URL nggak hard-code semua?

Karena local host dan container environment berbeda.

Contoh:

~~~text
local:
http://127.0.0.1:5000

compose:
http://mlflow:5000
~~~

Environment variable bikin application config bisa berubah tanpa edit source code.

---

## Non-root user

Image project pakai app user, bukan root untuk process application.

Kenapa?

Running everything as root adalah bad default dari security perspective.

Ini belum full production hardening, tapi ngajarin healthy habit.

---

## Docker bukan VM

Container share host kernel. Dia lebih lightweight daripada traditional VM.

VM biasanya virtualize full OS layer.

Container isolate process/environment di atas host kernel.

Kita nggak perlu terlalu deep ke namespace/cgroup di workshop, tapi jangan samakan persis Docker dengan VM.

---

## Docker solve apa, tidak solve apa?

Docker bantu:

~~~text
runtime consistency
dependency packaging
service isolation
delivery artifact
~~~

Docker tidak otomatis solve:

~~~text
bad code
bad model
data leakage
model drift
security vulnerability
poor architecture
~~~

Containerizing bad application cuma bikin bad application lebih gampang dipindah. 😭

---

## Checkpoint

Coba jawab:

1. Image beda apa dengan container?
2. Build time beda apa dengan run time?
3. Kenapa project kita punya beberapa target?
4. Bind mount vs named volume?
5. Kenapa API container akses mlflow:5000, bukan localhost:5000?
6. Docker solve problem apa?

Kalau ini kebayang, Docker Compose nanti jauh lebih gampang.
