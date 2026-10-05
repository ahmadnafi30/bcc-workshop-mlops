# Container Delivery — Dari Source Code Jadi Artifact yang Siap Dipakai Environment Lain

Setelah CI green, source code sudah verified.

Tapi deployment platform biasanya nggak mau clone repo lalu build random di production.

Kita ingin deliver artifact.

Project kita pilih Docker image sebagai artifact.

---

## Flow

~~~text
main commit
↓
CI success
↓
Container Delivery
↓
build image
↓
tag image
↓
push GHCR
~~~

GHCR = GitHub Container Registry.

---

## Kenapa build image lagi?

CI Docker build:

> “Can this image build successfully?”

Delivery Docker build:

> “Produce the artifact we actually publish.”

CD checkout exact tested commit.

Jadi:

~~~text
tested revision
=
published revision
~~~

Ini lineage.

---

## Image naming

Project punya separate image:

~~~text
...-api
...-mlflow
...-airflow
~~~

Kenapa separate?

Karena service responsibility beda.

Deployment target nanti bisa scale/update independently.

---

## Tag latest

Convenient:

~~~text
latest
~~~

Tapi pointer bergerak.

Hari ini latest = A.

Besok latest = B.

Useful buat casual pull, kurang ideal buat exact audit.

---

## SHA tag

~~~text
sha-abc123
~~~

Represent exact Git revision.

Kalau incident:

> “Image mana yang running?”

SHA tag lebih informative.

---

## Rollback application

Suppose image latest broken.

Deployment platform bisa pin previous SHA.

Ini application rollback.

Jangan confuse dengan model rollback.

### Application rollback

Docker image version.

### Model rollback

MLflow champion version.

MLOps punya dua version dimensions.

---

## Kenapa workshop berhenti di GHCR?

Karena kita belum define real target production environment.

Kalau kita tambahin:

~~~text
ssh fake-server
kubectl apply
~~~

tanpa environment real, itu theater.

Better teaching:

> Continuous Delivery selesai saat verified artifact siap di registry.

Nanti extension bisa deploy ke:

- VM,
- Cloud Run,
- ECS,
- Kubernetes.

---

## Artifact immutability

Idealnya published artifact tidak dimodifikasi diam-diam.

Kalau code berubah:

~~~text
new commit
→ new image
→ new tag/digest
~~~

Bukan edit container running manual.

Ini infrastructure hygiene.

---

## Checkpoint

1. Kenapa deployment artifact perlu?
2. CI build dan delivery build beda tujuan apa?
3. latest dan SHA tag tradeoff?
4. Application rollback beda apa dengan model rollback?
5. Kenapa workshop nggak fake auto-deploy?
