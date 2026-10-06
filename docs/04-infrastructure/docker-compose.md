# Docker Compose — Menyalakan Seluruh Stack Tanpa Jadi Operator Lima Terminal

Satu container masih gampang.

Tapi project kita punya beberapa service:

~~~text
MLflow
Airflow
FastAPI
Prometheus
Grafana
~~~

Kalau semuanya dijalankan manual, presenter harus ingat command start, port, environment variable, networking, storage, startup order, dan health dependency. Bayangin workshop baru mulai tapi layar presenter sudah penuh lima terminal. Belum ngomong materi, audience sudah capek duluan. 😭

Docker Compose masuk untuk mendefinisikan **multi-service environment** dalam satu file.

---

## Analogi: satu kompleks gedung

Kalau Docker image adalah blueprint satu unit, Compose seperti site plan satu kompleks.

Dia mendeskripsikan:

~~~text
service apa saja?
port mana dibuka?
network bagaimana?
storage mana dipakai?
dependency startup apa?
environment variable apa?
~~~

Semua ada di:

~~~text
docker-compose.yml
~~~

Jadi Compose bukan sekadar shortcut command. Dia adalah declarative definition dari local system architecture kita.

---

## Command utama

~~~bash
docker compose up -d --build
~~~

Kita bedah.

### up

Create dan start services.

### -d

Detached mode. Terminal balik ke kita, containers tetap running.

### --build

Build local image lebih dulu kalau ada perubahan yang butuh rebuild.

Jadi satu command ini sebenarnya melakukan coordination cukup banyak.

---

## Service 1 — MLflow

Host access:

~~~text
http://localhost:5000
~~~

Container lain access:

~~~text
http://mlflow:5000
~~~

Responsibility:

- experiment tracking;
- Model Registry;
- artifact access.

---

## Service 2 — FastAPI

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

### Menunggu MLflow siap

Healthcheck mengirim test readiness sederhana ke MLflow. Compose dapat menahan FastAPI sampai dependency itu siap; ini mengurangi race condition saat startup.

### Alamat dan tanggung jawab FastAPI

Buka `http://localhost:8000` dari browser host. API menyediakan health check, model info, prediction, dan metrics. FastAPI membutuhkan MLflow champion untuk melayani prediction.

---

## Service 3 — Airflow

Alamat Airflow di browser mengikuti port host pada output `docker compose ps airflow`. Contoh `127.0.0.1:18081->8080/tcp` berarti buka `http://localhost:18081`; port 8080 di kanan adalah port dalam container.

Responsibility:

- daily historical replay;
- initial training;
- model monitoring;
- optional retraining orchestration.

---

## Service 4 — Prometheus

Host:

~~~text
http://localhost:9090
~~~

Internal scrape target:

~~~text
api:8000/metrics
~~~

Prometheus tidak perlu keluar ke host lalu balik lagi. Dia langsung bicara ke API lewat Compose network.

---

## Service 5 — Grafana

Host:

~~~text
http://localhost:3000
~~~

Internal datasource:

~~~text
prometheus:9090
~~~

Jadi chain-nya:

~~~text
Grafana
↓
Prometheus
↓
FastAPI /metrics
~~~

---

## Host networking vs container networking

Ini bagian yang harus benar-benar kebayang.

Dari browser laptop:

~~~text
localhost:5000
~~~

artinya host port 5000 yang di-publish MLflow container.

Tapi dari API container:

~~~text
localhost:5000
~~~

artinya port 5000 **di API container sendiri**.

Bukan MLflow.

Untuk reach MLflow dari API:

~~~text
mlflow:5000
~~~

Docker Compose menyediakan DNS berdasarkan service name.

---

## Port mapping

Contoh:

~~~text
8000:8000
~~~

Kiri:

~~~text
host port
~~~

Kanan:

~~~text
container port
~~~

Flow:

~~~text
browser localhost:8000
↓
host port 8000
↓
FastAPI container port 8000
~~~

Kalau host port 8000 sudah dipakai Uvicorn lokal, Compose gagal bind.

Makanya sebelum step Docker, local FastAPI/MLflow/Airflow sebaiknya dihentikan dulu.

---

## Container running belum tentu application ready

Ini nuance penting.

Misalnya process MLflow baru start.

Docker bilang container running.

Tapi server mungkin masih initialize.

Jadi:

~~~text
container running
≠
application healthy
~~~

Kalau API terlalu cepat start dan langsung query MLflow, bisa kena connection error walaupun beberapa detik kemudian MLflow sebenarnya ready.

Makanya healthcheck useful.

---

## Cara Compose memastikan service siap

Healthcheck menjawab:

> “Service ini benar-benar ready menerima traffic nggak?”

Dengan health-aware dependency:

~~~text
MLflow starts
↓
healthcheck passes
↓
MLflow = healthy
↓
API boleh start
~~~

Ini mengurangi startup race condition.

---

## Berbagi file dataset antar-container

Kita bind mount:

~~~text
./data
→ /app/data
~~~

Benefit workshop:

~~~text
Airflow write processed data
↓
FastAPI read data yang sama
↓
host bisa inspect file yang sama
~~~

Satu local directory jadi simple shared storage.

Production besar mungkin pakai object storage, data lake, database, atau feature store. Tapi untuk workshop, bind mount bikin lifecycle terlihat dengan sangat jelas.

---

## Shared MLflow state — issue nyata hasil audit

Ini salah satu issue yang baru kelihatan setelah kita audit **end-to-end**, bukan per component.

Kalau local MLflow pakai storage A lalu Docker MLflow pakai storage B:

~~~text
train locally
↓
register model
↓
promote champion
↓
switch to Docker
↓
registry kosong
~~~

Participant pasti mikir:

> “Lho model saya hilang?”

Sebenarnya model tidak magically hilang. Dia ada di storage lain.

Makanya local helper dan Docker MLflow sekarang share:

~~~text
.mlflow/
~~~

Flow menjadi:

~~~text
local MLflow
↓
experiment + registry state
↓
stop local server
↓
Docker Compose mounts .mlflow
↓
state tetap ada
~~~

Ini contoh bagus bahwa system integration issue kadang tidak kelihatan kalau kita cuma test setiap komponen sendiri.

---

## Volume untuk menyimpan state service

Service lain punya internal state.

Contoh:

~~~text
airflow-home
prometheus-data
grafana-data
dvc-cache
~~~

Container sendiri disposable.

Kalau container dihapus lalu dibuat ulang, kita tidak selalu ingin data ikut hilang.

Volume memberi storage lifecycle terpisah dari process lifecycle.

---

## Bind mount vs named volume

### Bind mount

Host path explicit.

~~~text
./data → /app/data
~~~

Enak kalau kita perlu inspect file dari host.

### Named volume

Docker manage location.

~~~text
prometheus-data
~~~

Enak untuk internal service state yang tidak perlu kita buka manual.

Jadi bukan soal mana lebih bagus. Responsibility-nya beda.

---

## docker compose down

~~~bash
docker compose down
~~~

Stop/remove containers dan network.

Named volumes tetap.

---

## docker compose down -v

~~~bash
docker compose down -v
~~~

Tambahan **-v** remove named volumes.

Artinya Prometheus/Grafana/Airflow local state bisa reset.

Tapi bind-mounted folder **.mlflow/** tidak otomatis hilang karena dia folder host.

Ini command yang harus dipakai dengan sadar.

---

## Workspace service

Compose juga punya one-shot workspace:

~~~bash
docker compose run --rm workspace python scripts/doctor.py
~~~

Kenapa workspace tidak hidup terus?

Karena dia bukan long-running service.

Dia hanya environment untuk menjalankan project command.

Setelah command selesai, container di-remove.

---

## Compose profile

Workspace masuk optional profile.

Benefit-nya default stack tidak penuh service idle yang tidak dibutuhkan.

Pattern profile useful untuk:

- admin utility;
- debug tool;
- migration job;
- one-shot script.

---

## Environment variable dan configuration

Local:

~~~text
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
~~~

Compose:

~~~text
MLFLOW_TRACKING_URI=http://mlflow:5000
~~~

Source code sama, environment berbeda.

Configuration lewat environment variable bikin application lebih portable.

Kalau address di-hard-code dalam source, pindah environment jadi painful.

---

## docker compose ps

~~~bash
docker compose ps
~~~

Ini salah satu command first-aid.

Kita bisa lihat:

- container status;
- health;
- published ports.

Kalau stack “nggak jalan”, mulai dari sini sebelum random restart.

---

## Logs

~~~bash
docker compose logs -f api
~~~

Kalau API crash, baca error.

Jangan langsung conclude:

> “Modelnya rusak.”

Mungkin problem-nya:

~~~text
connection refused to MLflow
missing environment variable
permission denied
port conflict
~~~

Observability bukan cuma Grafana. Basic logs tetap penting.

---

## Compose bukan Kubernetes mini

Docker Compose sangat bagus untuk:

- local development;
- workshop;
- integration test;
- small single-host stack.

Kalau production perlu:

- multi-node scheduling;
- autoscaling;
- rolling deployment;
- advanced secrets;
- self-healing;
- sophisticated networking;

platform lain mungkin lebih appropriate.

Yang kita bawa dari Compose bukan claim bahwa semua production harus pakai Compose.

Yang kita bawa adalah konsep:

~~~text
service boundary
networking
storage
health
configuration
dependency
~~~

Itu transferable.

---

## Checkpoint

Coba jawab:

1. Docker Compose solve pain apa?
2. Kenapa localhost berbeda di host dan di container?
3. Apa arti mapping 8000:8000?
4. Container running dan application healthy beda apa?
5. Kenapa data pakai bind mount?
6. Kenapa Prometheus/Grafana cocok pakai volume?
7. Apa efek down -v?
8. Kenapa local MLflow dan Docker MLflow share state?
9. Workspace service itu buat apa?

Kalau clear, kalian bukan cuma bisa menjalankan Compose, tapi ngerti kenapa stack-nya dirancang seperti itu.
