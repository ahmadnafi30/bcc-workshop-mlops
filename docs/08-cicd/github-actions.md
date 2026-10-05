# GitHub Actions — Automating Repository Checks

## Workflow disimpan sebagai code

GitHub Actions workflow ada di:

~~~text
.github/workflows/
├── ci.yml
└── cd.yml
~~~

Ini penting karena automation itself version-controlled.

Kalau CI rule berubah, perubahan bisa direview seperti code lain.

---

# Event-driven

GitHub Actions mulai dari event.

Contoh:

~~~text
push
pull_request
workflow_run
workflow_dispatch
~~~

Workflow CI kita trigger saat branch relevant berubah.

Delivery trigger setelah CI main selesai sukses.

---

# Branch strategy

Repo kita:

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

Feature nggak langsung merge ke main.

Develop integration dulu.

---

# Branch policy job

Untuk Pull Request, CI check direction.

Allowed:

~~~text
feat/* → develop
fix/* → develop
docs/* → develop
chore/* → develop

develop → main
~~~

Kalau:

~~~text
feat/foo → main
~~~

branch policy fail.

Kenapa?

Supaya workflow repository nggak cuma ditulis di CONTRIBUTING, tapi juga automatically checked.

---

# Quality job

High-level:

~~~text
checkout repo
↓
install uv
↓
prepare Python
↓
uv sync --group docs
↓
Ruff
↓
pytest
↓
MkDocs strict build
~~~

---

# actions/checkout

Runner GitHub awalnya kosong.

Checkout action download repository content untuk commit yang sedang dites.

---

# setup-uv

Install uv di runner.

Kita pin action version.

Kenapa pin?

Automation dependency juga bisa berubah.

Version pin mengurangi surprise.

---

# Ruff

~~~bash
uv run ruff check src api scripts tests
~~~

Fast static lint.

---

# pytest

~~~bash
uv run pytest -q
~~~

Unit/API logic tests.

---

# MkDocs strict

~~~bash
uv run --group docs mkdocs build --strict
~~~

Strict mode bikin docs warning tertentu fail build.

Bagus buat workshop repo karena broken reference jangan lolos diam-diam.

---

# Docker matrix

Kita punya target:

~~~text
api
mlflow
airflow
~~~

Daripada copy job 3 kali, GitHub Actions matrix:

~~~text
same job template
×
three target values
~~~

Runner build each.

---

# Cache

Docker Buildx dan uv bisa pakai cache.

Benefit:

- faster repeated runs,
- less download/build.

Tapi important:

> Cache is optimization, not correctness dependency.

Workflow harus tetap bisa run from empty cache.

---

# Concurrency

Kalau commit A sedang CI lalu commit B push ke branch sama, run A bisa obsolete.

CI config cancel in-progress run untuk same group.

Ini save runner time.

---

# CD workflow

Setelah CI main success:

~~~text
workflow_run
↓
Container Delivery
~~~

CD ensure event:

- CI success,
- push event,
- branch main.

PR saja tidak publish release image.

---

# GHCR login

GHCR = GitHub Container Registry.

Workflow pakai:

~~~text
GITHUB_TOKEN
~~~

dengan permission:

~~~text
packages: write
~~~

Kita nggak perlu simpan personal Docker password.

---

# Image metadata

Published image dapat tags seperti:

~~~text
latest
sha-abcdef
~~~

latest convenient.

SHA traceable.

---

# Kenapa exact SHA useful?

Kalau latest berubah setiap release:

~~~text
today latest = commit A
tomorrow latest = commit B
~~~

Rollback/audit butuh fixed reference.

SHA tag memberi exact application revision.

---

# Secrets

Rule basic:

> Jangan taruh secret literal di YAML.

Use:

- GitHub Secrets,
- environment secret,
- workload identity,

depending deployment.

Workshop tidak membutuhkan external cloud credential.

---

# Cara baca workflow YAML sebagai newbie

Jangan baca semua sekaligus.

Urutan:

1. name
2. on / trigger
3. permissions
4. jobs
5. one job
6. steps
7. expressions

Pelan-pelan.

YAML CI terlihat scary mostly karena nested structure, bukan karena concept-nya selalu rumit.
