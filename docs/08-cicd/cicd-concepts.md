# CI/CD — What Happens After We Push Code?

## MLOps project tetap software project

Walaupun ada model, data, dan MLflow, source code tetap berubah.

Misalnya kita update:

- feature logic,
- API,
- DAG,
- Dockerfile,
- docs.

Pertanyaan:

> “Sebelum perubahan ini masuk stable branch, siapa yang memastikan project masih sehat?”

Kalau jawabannya:

> “Semoga contributor ingat run semua tests.”

kurang kuat.

Kita butuh automated quality gate.

---

# CI — Continuous Integration

Dalam workshop, CI menjawab:

> **“Is this repository change safe enough to integrate?”**

Saat push/PR:

~~~text
code change
   ↓
Ruff
   ↓
pytest
   ↓
MkDocs build
   ↓
Docker Compose config
   ↓
Docker image builds
~~~

Kalau fail:

~~~text
❌
do not treat as healthy integration
~~~

---

# Kenapa lint masuk CI?

Lint seperti Ruff catch:

- unused import,
- syntax-ish issue,
- import ordering,
- code quality rules.

Apakah lint prove code correct?

No.

Tapi dia enforce basic consistency.

---

# Kenapa tests?

Tests verify behavior.

Feature engineering test misalnya ensure lag/rolling semantics benar.

API test ensure endpoint contract.

Monitoring test ensure retraining threshold behavior.

---

# Kenapa docs juga dibuild?

Karena docs adalah deliverable utama workshop.

Broken nav atau invalid config harus ketahuan sebelum presenter buka docs saat event.

Jadi docs bukan second-class citizen.

---

# Kenapa Docker build di CI?

Python tests bisa pass tapi Dockerfile broken.

Contoh:

~~~text
COPY path wrong
dependency missing in image
build stage fail
~~~

Docker build validation catch packaging issue.

---

# CD punya dua arti

CD sering berarti salah satu:

## Continuous Delivery

~~~text
verified code
↓
build artifact
↓
publish artifact
↓
ready to deploy
~~~

## Continuous Deployment

~~~text
verified code
↓
build
↓
publish
↓
automatically deploy to production
~~~

Workshop kita pakai **Continuous Delivery**.

Kita publish image ke GHCR.

Belum auto deploy ke server/cloud.

---

# Kenapa nggak pura-pura deploy?

Karena kita belum punya actual production destination.

Daripada menambah:

~~~text
ssh example.com
docker pull
restart
~~~

yang nggak benar-benar dipakai, kita stop di boundary yang honest:

~~~text
deployable container artifact
available in registry
~~~

Nanti target infrastructure bisa ditambah.

---

# Software artifact vs model artifact

Ini subtle tapi penting.

## Application artifact

~~~text
Docker image
~~~

Versioned by Git commit / image tag.

## Model artifact

~~~text
MLflow model version
~~~

Versioned by Model Registry.

Jadi production-like system punya dua independent version axis:

~~~text
application version
and
model version
~~~

API code bisa sama tapi champion berubah.

Champion sama tapi API code bisa update.

---

# Analogi factory

CI = quality inspection.

CD = packaging approved product into warehouse.

Continuous Deployment = automatically shipping from warehouse to customer.

Simple mental model.

---

# Airflow vs CI/CD

Again:

~~~text
Airflow
→ operational ML/data workflow

GitHub Actions
→ repository delivery workflow
~~~

Dua-duanya automation, trigger-nya beda.

---

# Checkpoint

Kalau ditanya:

> “CI/CD di project ini ngapain?”

jawaban nggak harus panjang.

Cukup:

> CI automatically verifies code/docs/container changes. CD publishes tested container images to GHCR after main passes CI.

Clear.
