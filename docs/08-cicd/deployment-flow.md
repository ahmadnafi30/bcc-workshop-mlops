# Container Delivery — From Tested Code to GHCR

## Setelah CI hijau, what next?

Code sudah verified.

Sekarang kita mau produce reusable runtime artifact.

Artifact-nya:

~~~text
Docker image
~~~

Flow:

~~~text
main commit
↓
CI success
↓
Container Delivery
↓
build exact revision
↓
tag
↓
push GHCR
~~~

---

# Image kita

Separate images:

~~~text
bcc-workshop-mlops-api
bcc-workshop-mlops-mlflow
bcc-workshop-mlops-airflow
~~~

Mereka dibuild dari target Dockerfile berbeda.

---

# latest tag

Convenient:

~~~text
latest
~~~

Tapi movable.

Hari ini menunjuk commit A.

Besok commit B.

Jadi jangan rely on latest untuk precise audit.

---

# SHA tag

Contoh:

~~~text
sha-a1d7567
~~~

Trace ke exact Git commit.

Benefit:

- rollback,
- audit,
- reproducibility,
- deployment trace.

---

# Kenapa CD build lagi kalau CI sudah build?

Good question.

CI build:

> Can this image build successfully?

CD build:

> Build artifact that will actually be published.

CD checkout exact tested commit.

Jadi published artifact berasal dari revision yang sudah lolos quality gate.

---

# GHCR sebagai warehouse

Analogi factory:

~~~text
CI
→ quality inspection

Docker build
→ packaging

GHCR
→ warehouse
~~~

Deployment platform nanti tinggal pull image.

---

# Kita belum Continuous Deployment

Workflow berhenti di GHCR.

Belum ada:

- VPS restart,
- Kubernetes rollout,
- Cloud Run deploy.

Jadi terminology kita:

~~~text
Continuous Delivery
~~~

Bukan full Continuous Deployment.

---

# App version vs model version

Ini perlu banget dipahami.

Misalnya:

~~~text
API image:
sha-a1d7567

Champion model:
version 5
~~~

Besok model promote ke version 6.

API image masih sama.

Atau API bug fix deploy image baru.

Champion masih version 6.

Mereka independent.

MLOps observability ideal harus bisa trace both.

---

# Future extension

Kalau punya target server, flow bisa extend:

~~~text
GHCR
↓
deployment platform
↓
health check
↓
traffic
~~~

Tapi workshop stop sebelum infrastructure-specific detail.

Itu intentional.
