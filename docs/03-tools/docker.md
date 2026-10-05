# Docker — Making Runtime More Predictable

## “Di laptopku jalan.”

Kalimat paling classic di software development 😄

Project Python bisa jalan di laptop A tapi fail di laptop B karena Python version, package version, environment variable, atau system dependency berbeda.

uv sudah membantu Python environment.

Tapi saat application mulai terdiri dari beberapa service, kita butuh runtime packaging yang lebih consistent.

Masuk Docker.

---

# Docker secara sederhana

Docker memungkinkan kita build **image** yang mendefinisikan environment application.

Image kemudian bisa dijalankan menjadi **container**.

~~~text
Dockerfile
   ↓ build
Image
   ↓ run
Container
~~~

---

# Image vs Container

## Image

Template / packaged artifact.

Belum running.

## Container

Running instance dari image.

Analogi sederhana:

~~~text
Class
→ Image

Object instance
→ Container
~~~

Nggak 100% exact, tapi cukup buat mental model.

---

# Dockerfile

Project punya:

~~~text
docker/Dockerfile
~~~

Instruction penting:

## FROM

Base image.

## WORKDIR

Working directory di image.

## COPY

Copy project file.

## RUN

Command saat image build.

## ENV

Environment variable.

## CMD

Default command saat container start.

---

# Build-time vs run-time

## Build-time

Saat docker build.

Docker execute Dockerfile dan menghasilkan image.

## Run-time

Saat container start.

CMD dijalankan.

Kalau source berubah tapi image belum rebuild, container masih bisa pakai code lama.

---

# Multi-target design

Satu Dockerfile punya target:

~~~text
base
├── api
├── mlflow
└── airflow
~~~

Shared setup ada di base.

Masing-masing service punya startup behavior berbeda.

---

# Kenapa service dipisah?

Karena responsibility beda.

~~~text
API
→ serving

MLflow
→ tracking + registry

Airflow
→ orchestration
~~~

Kalau semua satu container, lifecycle jadi coupled.

Separate container membuat boundary lebih jelas.

---

# Bind mount vs named volume

## Bind mount

Host folder langsung mounted.

Contoh:

~~~text
./data
→ /app/data
~~~

Useful karena hasil Airflow langsung terlihat di host dan API membaca data yang sama.

## Named volume

Docker-managed storage.

Contoh:

~~~text
airflow-home
prometheus-data
grafana-data
~~~

Useful buat service state.

---

# Shared MLflow state

Workshop punya:

~~~text
./.mlflow
~~~

yang mounted ke MLflow container.

Tujuannya:

~~~text
train locally
↓
register champion
↓
switch to Compose
↓
champion still exists
~~~

Jadi flow workshop nggak putus.

---

# Networking

localhost di dalam container berarti container itu sendiri.

Untuk reach service lain, Compose menyediakan service name.

~~~text
API
→ http://mlflow:5000

Prometheus
→ http://api:8000/metrics

Grafana
→ http://prometheus:9090
~~~

Ini salah satu confusion paling common.

---

# Port publishing

Misalnya:

~~~text
5000:5000
~~~

Artinya host port 5000 diteruskan ke container port 5000.

Makanya browser host bisa buka localhost:5000.

---

# Non-root user

Application image jalan sebagai user non-root.

Ini good default karena kita tidak perlu memberi privilege root ke process application.

Bukan full hardening, tapi lebih proper.

---

# .dockerignore

Docker build context bisa besar kalau semua file dikirim.

.dockerignore exclude hal seperti:

- .git,
- .venv,
- data,
- caches,
- local MLflow state.

Build context jadi lebih kecil dan lebih aman.

---

# Docker bukan magic

Docker tidak solve:

- code bug,
- data leakage,
- bad model,
- drift,
- insecure credential.

Docker mainly membantu packaging dan environment consistency.

---

# Manual build

~~~bash
docker build   -f docker/Dockerfile   --target api   -t bcc-mlops-api .
~~~

Tapi workshop sehari-hari pakai Compose karena service kita saling terhubung.
