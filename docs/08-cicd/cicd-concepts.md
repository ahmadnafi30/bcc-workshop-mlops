# CI/CD — Biar Quality Nggak Bergantung ke “Guys Jangan Lupa Run Test”

Bayangin repo mulai dikerjakan beberapa orang.

Sebelum merge, idealnya semua contributor:

- run tests;
- run lint;
- build docs;
- validate Docker;
- build images.

Kalau process-nya cuma:

> “Jangan lupa ya sebelum push.”

Cepat atau lambat pasti ada yang lupa. Termasuk kita sendiri. 😭

CI masuk supaya quality gate menjadi **repeatable automation**, bukan checklist di kepala manusia.

---

# Continuous Integration — integrate apa?

Kata Integration penting.

Setiap developer kerja di branch.

Code masing-masing mungkin works sendiri.

Masalah mulai muncul ketika perubahan digabung.

CI membantu jawab:

> “Repository state ini masih sehat nggak setelah perubahan ini masuk?”

Jadi CI lebih luas dari sekadar pytest.

---

# Quality flow project kita

~~~text
Push / Pull Request
        ↓
Branch Policy
        ↓
Setup uv + Python
        ↓
Ruff
        ↓
pytest
        ↓
MkDocs strict build
        ↓
Docker Compose validation
        ↓
Docker image build
~~~

Kenapa banyak?

Karena repo kita bukan cuma Python code.

Workshop docs dan container setup juga deliverable.

---

# Ruff

Saat audit sebelumnya, CI kita benar-benar menemukan import-order issue.

Runtime impact-nya kecil.

Tapi lint automation bikin style consistency tidak perlu dibahas manual saat review.

Benefit:

> Reviewer fokus ke logic, bukan mechanical style.

---

# pytest

Test menjaga behavior yang sudah kita expect.

Contoh:

- lag feature tidak cross-zone;
- rolling feature tidak leak target;
- API schema valid;
- healthy model tidak retrain.

Test bukan bukti bahwa system sempurna.

Dia safety net terhadap regression yang kita tahu.

---

# Kenapa MkDocs strict build masuk CI?

Karena docs adalah product.

Workshop bisa gagal walaupun Python perfect kalau:

~~~text
navigation broken
page missing
link salah
~~~

Makanya docs punya quality gate sendiri.

Ini especially penting karena repository ini memang ditujukan untuk teaching, bukan cuma application runtime.

---

# Kenapa Docker image build masuk CI?

Python test bisa green tapi Dockerfile fail.

Contoh:

~~~text
COPY path salah
dependency nggak ikut image
target build rusak
~~~

Kalau baru ketahuan pas release, terlalu telat.

CI build image lebih awal.

---

# Branch strategy

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

## Feature/docs/fix branch

Tempat iterate.

## Develop

Integration branch.

Beberapa changes yang individually green ketemu di sini.

## Main

Stable workshop release.

Branch yang harus nyaman dipakai presenter dan participant.

---

# Kenapa tidak langsung feat → main?

Bayangin feature A mengubah API schema.

Feature B mengubah monitoring parser.

Masing-masing mungkin green dari base lama.

Saat digabung bisa muncul behavior conflict.

Develop memberi integration boundary sebelum stable release.

---

# Branch policy as code

CI check arah PR.

Allowed:

~~~text
feat/*  → develop
fix/*   → develop
docs/*  → develop
chore/* → develop

develop → main
~~~

Kalau:

~~~text
feat/foo → main
~~~

branch-policy job fail.

Workflow tidak cuma ditulis di README. Ada automated check.

---

# CI check vs GitHub branch protection

CI bisa bilang:

~~~text
branch policy failed
~~~

Tapi kalau platform permission masih allow bypass, admin secara teknis bisa tetap merge.

Ruleset/branch protection memberi enforcement di platform level.

Jadi:

~~~text
CI
→ verify condition

branch protection
→ restrict action
~~~

Dua-duanya complement.

---

# CD — satu singkatan dua arti

### Continuous Delivery

~~~text
verified source
↓
build artifact
↓
publish artifact
↓
ready to deploy
~~~

### Continuous Deployment

~~~text
verified source
↓
build artifact
↓
publish
↓
automatically deploy production
~~~

Karena repo belum punya real production target.

Kenapa belum deployment?

Karena kita tidak punya real production target environment.

Lebih baik jujur berhenti di GHCR daripada menambahkan command deployment palsu hanya supaya diagram kelihatan penuh.

---

# GHCR sebagai artifact registry

Container image adalah deployable software artifact.

Kita publish image:

~~~text
API
MLflow
Airflow
~~~

ke GitHub Container Registry.

Nanti deployment platform tinggal pull exact image.

---

# latest vs SHA tag

### latest

Convenient.

Tapi pointer berubah.

~~~text
hari ini latest = commit A
besok latest = commit B
~~~

### SHA tag

Map ke exact source revision.

~~~text
sha-a1b2c3
~~~

Kalau incident:

> “Image ini dibangun dari source mana?”

SHA tag jauh lebih useful.

---

# Code version vs model version

Ini sangat penting di MLOps.

Kita punya dua version dimension.

### Application version

~~~text
Git commit
Docker image
~~~

### Model version

~~~text
MLflow model version
champion alias
~~~

Bisa terjadi:

~~~text
Docker image sama
model champion berubah
~~~

atau:

~~~text
Docker image berubah
champion tetap
~~~

Dua lifecycle ini related tapi independent.

---

# Rollback juga ada dua

### Application rollback

Deploy image SHA sebelumnya.

### Model rollback

Move champion alias ke old model version.

Kalau system incident, kita harus tahu layer mana yang problem.

Jangan rollback semuanya tanpa diagnosis.

---

# GitHub Actions vs Airflow

Dua-duanya automation, tapi trigger domain berbeda.

~~~text
GitHub Actions
→ repository event

Airflow
→ data / ML workflow event
~~~

Contoh:

~~~text
new pull request
→ GitHub Actions

new taxi batch
→ Airflow
~~~

Mereka bukan duplicate tool.

---

# Fresh runner itu justru bagus

GitHub Actions runner mulai dari environment fresh.

Kalau project cuma jalan karena laptop developer punya hidden dependency, CI akan expose itu.

Fresh environment adalah reproducibility pressure test.

---

# Secrets

Registry publishing butuh auth.

Rule:

> Credential jangan masuk source control.

Gunakan scoped token / secret management.

Project pakai GitHub-provided token dengan permission yang dibutuhkan.

---

# Checkpoint

Coba jawab:

1. CI sebenarnya verify apa?
2. Kenapa lint, tests, docs, dan Docker sama-sama masuk?
3. Kenapa develop useful?
4. CI branch policy beda apa dengan platform ruleset?
5. Delivery beda apa dengan Deployment?
6. latest dan SHA tag tradeoff-nya apa?
7. Application version dan model version beda apa?
8. GitHub Actions beda apa dengan Airflow?

Kalau clear, CI/CD sudah nggak lagi sekadar YAML yang “pokoknya jalan”.
