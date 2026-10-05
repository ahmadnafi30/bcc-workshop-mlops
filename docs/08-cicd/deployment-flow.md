# Container Delivery — Dari Source Code ke Artifact yang Siap Dipakai

Setelah CI green, source code sudah verified.

Tapi production/deployment platform biasanya tidak ideal kalau harus:

~~~text
git clone
install dependency
build random state
start app
~~~

langsung di target environment.

Kita ingin satu artifact yang sudah dibangun dan bisa dipull.

Project kita pakai Docker image sebagai delivery artifact.

---

# Flow

~~~text
main commit
↓
CI success
↓
Container Delivery
↓
build exact revision
↓
tag image
↓
push GHCR
~~~

GHCR = GitHub Container Registry.

Think of it as warehouse untuk container images.

---

# Kenapa build image lagi setelah CI?

CI build menjawab:

> “Image ini bisa dibuild nggak?”

Delivery build menjawab:

> “Buat artifact yang benar-benar akan kita publish.”

Yang penting kedua proses refer ke same source revision.

---

# Image per service

Kita publish separate image:

~~~text
...-api
...-mlflow
...-airflow
~~~

Kenapa?

Karena service punya responsibility dan runtime lifecycle berbeda.

Di deployment target nanti, API bisa di-update tanpa harus replace Airflow worker misalnya.

---

# Tag

Image tanpa meaningful tag sulit ditrace.

Kita punya:

~~~text
latest
sha-<commit>
~~~

### latest

Convenience pointer.

### sha

Exact revision identity.

Kalau mau deterministic deployment/rollback, SHA jauh lebih kuat.

---

# Digest

Selain tag, container registry juga punya content digest.

Digest merepresentasikan actual image content.

Dalam production serious, digest pinning bisa memberi immutability lebih kuat.

Workshop cukup fokus ke SHA tag sebagai bridge Git lineage.

---

# Rollback

Suppose release baru API punya bug.

Kalau deployment platform menyimpan old SHA:

~~~text
sha-new
↓ problem
sha-old
↓ redeploy
~~~

Itu application rollback.

Ingat, beda dengan model rollback.

---

# Kenapa belum auto deploy?

Karena deployment membutuhkan target nyata.

Pertanyaan production deployment biasanya:

- server mana?
- credentials bagaimana?
- health rollout bagaimana?
- rollback bagaimana?
- network policy?
- secrets?
- domain/TLS?
- scale?

Kalau kita belum punya environment real, menulis command deploy palsu tidak menambah learning yang meaningful.

Workshop berhenti saat artifact sudah siap.

---

# Checkpoint

1. Kenapa kita butuh delivery artifact?
2. Kenapa published revision harus sama dengan tested revision?
3. Kenapa image service dipisah?
4. latest vs SHA?
5. Application rollback beda apa dengan model rollback?
6. Kenapa workshop berhenti di GHCR?
