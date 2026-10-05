# Container Delivery — Dari Source Code Sampai Artifact yang Bisa Dipull

CI kita sudah menjawab:

> “Revision ini lolos quality checks dan image bisa dibuild.”

Tapi deployment target tidak ideal kalau setiap release harus:

~~~text
git clone
install uv
sync dependencies
build source
guess environment
start process
~~~

langsung di server.

Kita ingin satu **built artifact** yang sudah punya runtime package jelas.

Untuk application kita, artifact itu Docker image.

---

# Analogi: source recipe vs packaged product

Git repository seperti resep + bahan desain.

Container image seperti product yang sudah dipack.

Deployment platform seharusnya menerima:

~~~text
artifact exact
~~~

bukan mengulang build process secara improvisasi.

Ini membantu consistency antara environments.

---

# Full delivery flow

~~~text
develop
↓ PR
main
↓
CI
↓ success
Container Delivery
↓
checkout exact tested commit
↓
build service image
↓
tag
↓
push GHCR
~~~

GHCR = GitHub Container Registry.

Anggap sebagai warehouse image.

---

# Kenapa delivery hanya dari main?

Branch lain masih development/integration.

Kalau setiap feature push publish latest production-ish image:

~~~text
feat/a
feat/b
docs/c
~~~

registry jadi noisy dan release semantics tidak jelas.

Main merepresentasikan stable release branch.

Jadi delivery condition:

~~~text
CI success
AND
branch main
AND
push event
~~~

---

# Kenapa PR tidak publish image?

Pull request code belum merged.

Dia candidate change.

CI boleh build ephemeral image untuk verify.

Tapi publish release artifact sebaiknya setelah stable integration.

Separation:

~~~text
PR
→ verify

main
→ deliver
~~~

---

# Exact tested commit

Ini critical.

Wrong flow:

~~~text
CI tests commit A
↓
main advances to commit B
↓
CD builds latest HEAD B
~~~

Sekarang:

~~~text
tested revision
≠
published revision
~~~

Bad lineage.

Correct:

~~~text
CI passes commit A
↓
workflow gives commit SHA A
↓
CD checkout A
↓
build A
↓
publish A
~~~

Jadi evidence CI match artifact.

---

# Kenapa build lagi di delivery?

CI image build bisa hanya validation:

> “Dockerfile target ini buildable.”

Delivery build produce image yang benar-benar dikirim registry.

Kita bisa optimize dengan shared cache, but semantic purpose beda.

Potential advanced pattern:

- build once;
- sign/promote same artifact;
- avoid duplicate build.

Workshop keep workflow understandable.

---

# Image per service

Project punya:

~~~text
api
mlflow
airflow
~~~

Kenapa tidak satu mega image?

Service punya:

- dependency profile beda;
- startup command beda;
- release lifecycle beda;
- scaling need beda.

API code change mungkin tidak perlu roll Airflow.

Separate image memberi deployment flexibility.

---

# Image naming

Pattern:

~~~text
ghcr.io/<owner>/bcc-workshop-mlops-api
ghcr.io/<owner>/bcc-workshop-mlops-mlflow
ghcr.io/<owner>/bcc-workshop-mlops-airflow
~~~

Name harus identify service.

Kalau semua bernama:

~~~text
mlops:latest
~~~

kita kehilangan clarity.

---

# Tag latest

~~~text
latest
~~~

Useful buat convenience.

Contoh local:

~~~text
docker pull ...:latest
~~~

Tapi latest mutable.

Hari ini pointing A.

Besok B.

Jadi latest bukan identity immutable.

---

# Tag SHA

~~~text
sha-a1b2c3...
~~~

Bridge ke Git commit.

Kalau incident:

> “Image production dibangun dari source mana?”

Tag memberi clue direct.

Ini software lineage.

---

# Tag vs digest

Tag adalah human-friendly pointer/name.

Digest adalah content-addressed identity image.

Tag bisa berpindah.

Digest immutable untuk exact image content.

Production high-assurance deployment kadang pin digest.

Workshop fokus SHA tag karena gampang connect source history.

---

# Registry permissions

CD perlu push package.

GitHub Actions menggunakan scoped permission.

Rule:

> Jangan hard-code personal Docker/GitHub password ke workflow.

Credential management adalah part delivery security.

---

# Public vs private package

Container registry package visibility bisa public/private tergantung repo/org setup.

Kalau deployment target external perlu pull private image, dia butuh auth.

Workshop tidak deep ke IAM, tapi participant perlu tahu:

> “Image ada di registry” tidak otomatis berarti semua machine boleh pull.

---

# Delivery vs Deployment

Ini distinction utama.

### Delivery

~~~text
artifact built
↓
published
↓
ready to deploy
~~~

### Deployment

~~~text
artifact selected
↓
placed into target environment
↓
service started/rolled out
↓
health verified
~~~

Workshop selesai di Delivery.

---

# Kenapa tidak fake deployment?

Karena target deployment nyata butuh decision:

- VM atau cloud service?
- networking?
- TLS?
- secret?
- scaling?
- health rollout?
- zero downtime?
- rollback?
- observability?
- cost?

Kalau kita cuma tambah:

~~~bash
ssh server
docker pull latest
docker run ...
~~~

tanpa actual environment, peserta bisa mendapat false impression deployment sesederhana itu.

Lebih baik boundary jujur.

---

# Kalau nanti deploy ke VPS?

Possible future:

~~~text
GHCR image SHA
↓
server authenticate registry
↓
pull exact SHA tag
↓
run container
↓
health check
↓
reverse proxy/TLS
~~~

Masih perlu secret/network/rollback design.

---

# Kalau deploy ke Kubernetes?

Flow concept sama:

~~~text
GHCR image
↓
Deployment manifest
↓
cluster pulls
↓
pods roll
↓
readiness check
↓
traffic
~~~

Tool beda.

Artifact lineage tetap penting.

---

# Application rollback

Suppose new API image bug.

Current:

~~~text
sha-new
~~~

Previous good:

~~~text
sha-old
~~~

Rollback:

~~~text
deployment target
↓
select sha-old
↓
restart/rollout
~~~

No need rebuild old source.

Registry sudah punya artifact.

---

# Model rollback beda

Suppose application image sehat, tapi champion model v5 jelek.

Tidak perlu rollback Docker image.

Kita bisa:

~~~text
champion alias
v5 → v3
~~~

Jadi MLOps punya dua rollback dimensions:

~~~text
application artifact
model artifact
~~~

Diagnosis harus menentukan layer.

---

# Example incident reasoning

### Incident A

~~~text
HTTP endpoint crashes after code change
model unchanged
~~~

Likely application rollback.

### Incident B

~~~text
API healthy
latency normal
recent MAE spikes after model promotion
~~~

Likely model rollback/investigation.

### Incident C

~~~text
new image + new champion released together
system bad
~~~

More complex.

This is why changing too many dimensions simultaneously makes diagnosis harder.

---

# Release coupling

Mature system kadang decouple app release dan model release.

Project kita sudah menunjukkan pattern itu:

~~~text
Docker image version
independent from
MLflow champion alias
~~~

Benefit:

- model can promote without rebuilding API;
- API bugfix can deploy without retraining model.

Loose coupling.

---

# Artifact retention

Kalau registry hanya menyimpan latest dan menghapus semua old SHA, rollback capability hilang.

Production retention policy harus balance:

- storage cost;
- rollback need;
- compliance;
- audit history.

Workshop registry kecil, tapi concept worth knowing.

---

# Image vulnerability/security

Built artifact juga perlu security.

Future CI bisa tambah:

- image scanning;
- SBOM;
- signing;
- provenance;
- dependency vulnerability check.

MLOps delivery tetap software supply-chain problem.

Workshop belum implement semua, tapi architecture bisa berkembang ke sana.

---

# Delivery evidence

Idealnya kita bisa trace:

~~~text
GHCR image
↓
tag SHA
↓
Git commit
↓
CI run
↓
tests/build result
~~~

Ini software artifact lineage.

Compare model lineage:

~~~text
champion
↓
model version
↓
MLflow run
↓
snapshot fingerprint
~~~

Dua lineage chain berjalan berdampingan.

---

# Checkpoint

1. Kenapa deployment target sebaiknya pull built artifact, bukan build improvisasi?
2. Kenapa delivery hanya setelah main + CI?
3. PR image build dan release image publishing beda purpose apa?
4. Kenapa exact tested commit harus dipublish?
5. Kenapa service image dipisah?
6. latest dan SHA tag beda semantics?
7. tag dan digest beda apa?
8. Delivery vs Deployment?
9. Kenapa workshop tidak fake auto-deploy?
10. Application rollback vs model rollback?
11. Kenapa app release dan model promotion bagusnya loosely coupled?
12. Artifact retention relate ke rollback bagaimana?
13. Future security checks apa yang bisa ditambah?
14. Software lineage chain dan model lineage chain beda apa?

Kalau ini clear, GHCR bukan lagi sekadar “tempat upload Docker image”, tapi bagian dari traceable software delivery lifecycle.
