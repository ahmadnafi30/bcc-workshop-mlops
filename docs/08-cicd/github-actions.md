# GitHub Actions — Membaca Workflow Tanpa Tenggelam di YAML

GitHub Actions adalah automation platform yang hidup dekat dengan repository.

Begitu ada event seperti pull request atau push, workflow bisa jalan.

Kalau pertama kali buka file YAML CI, mungkin kelihatan panjang banget. Cara bacanya jangan dari setiap syntax kecil dulu.

Baca dari struktur besar.

~~~text
name
↓
trigger
↓
permissions
↓
jobs
↓
steps
~~~

Setelah mental model ini jelas, expression detail jauh lebih gampang.

---

## Workflow

File ada di:

~~~text
.github/workflows/
~~~

Project kita punya:

~~~text
ci.yml
cd.yml
~~~

Workflow = satu automation definition.

---

## Trigger

Workflow CI bisa jalan karena:

~~~text
push
pull_request
manual dispatch
~~~

CD kita bergantung pada successful CI di main.

Event-driven behavior ini beda dengan Airflow schedule/data pipeline trigger.

---

## Job

Workflow punya jobs.

Contoh:

~~~text
Python + docs quality
Docker build - api
Docker build - mlflow
Docker build - airflow
~~~

Jobs bisa parallel.

Kalau API image build lambat, MLflow build nggak harus menunggu selama dependency-nya memang independen.

---

## Step

Di dalam job ada steps.

Quality job misalnya:

~~~text
checkout
setup uv
install Python
sync dependency
Ruff
pytest
MkDocs
~~~

Steps dalam satu job jalan berurutan.

---

## Checkout

Runner fresh belum punya repository.

Checkout ambil exact revision yang mau dites.

Ini penting buat lineage:

~~~text
PR commit
↓
exact checkout
↓
checks
~~~

---

## Setup uv + Python

CI environment sebaiknya sedekat mungkin dengan local developer flow.

Kalau local pakai uv tapi CI punya totally different install logic, divergence lebih mudah terjadi.

Goal bukan environment identical 100%, tapi setup path harus konsisten enough untuk catch real issue.

---

## Branch Policy Job

Job ini cuma relevant pada pull request.

Dia baca:

~~~text
base branch
head branch
~~~

Lalu validate direction.

Contoh:

~~~text
docs/foo → develop
✅

develop → main
✅

feat/foo → main
❌
~~~

Ini contoh simple process-as-code.

---

## Matrix build

Daripada:

~~~yaml
job_api:
  ...

job_mlflow:
  ...

job_airflow:
  ...
~~~

yang isinya almost sama, matrix bilang:

~~~text
target = [api, mlflow, airflow]
~~~

Lalu same job template dijalankan per target.

Benefit:

- less duplication;
- same build logic;
- gampang tambah target;
- parallelism.

---

## Cache

CI bisa cache uv dependency atau Docker layer.

Cache bikin lebih cepat.

Tapi jangan sampai workflow cuma works kalau cache ada.

Rule:

> Cache is optimization, not correctness dependency.

Kalau cache clear, build tetap harus bisa sukses.

---

### Docker cache

Suppose kalian push commit A.

CI A mulai.

30 detik kemudian push commit B.

CI A mungkin sudah obsolete.

Concurrency config bisa cancel older run dari branch yang sama.

Benefit:

- hemat runner time;
- feedback lebih fokus ke latest revision.

---

## Permissions

Workflow punya permission explicit.

Container delivery perlu write package.

Quality check cuma butuh read source.

Least privilege lebih sehat daripada semua workflow diberi write access.

---

## GITHUB_TOKEN

GitHub menyediakan token temporary buat workflow.

Untuk GHCR, token bisa dipakai sesuai permission.

Kenapa better daripada personal password?

- lifecycle managed;
- scoped;
- tidak hard-code;
- tidak perlu share credential personal.

---

## CD Workflow

Flow:

~~~text
CI on main
↓
success?
├── no  → stop
└── yes → Container Delivery
           ↓
           build exact commit
           ↓
           login GHCR
           ↓
           push image
~~~

Jadi release artifact tidak dibuat dari arbitrary unverified revision.

---

## Kenapa exact tested commit?

Bayangin CI test commit A.

Tapi CD build HEAD terbaru commit B yang belum dites.

Sekarang:

~~~text
tested code
≠
published code
~~~

Bad lineage.

Makanya delivery harus checkout exact revision yang passed CI.

---

## Cara debug GitHub Actions

Jangan hanya lihat:

~~~text
red ❌
~~~

Buka job.

Cari step pertama yang fail.

Contoh:

~~~text
Ruff failed
→ style/import problem

pytest failed
→ behavior/test regression

MkDocs failed
→ documentation config/page issue

Docker build failed
→ image packaging issue
~~~

Nama step membantu narrow root cause.

---

## Checkpoint

1. Workflow, job, step beda apa?
2. Trigger digunakan buat apa?
3. Kenapa fresh runner useful?
4. Matrix build solve duplication apa?
5. Cache itu optimization atau correctness?
6. Kenapa permission perlu scoped?
7. Kenapa CD build exact tested commit?
8. Kalau workflow merah, debugging mulai dari mana?
