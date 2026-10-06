# Step 8 — CI/CD: Dari “Semoga Semua Orang Run Test” Jadi Quality Gate yang Konsisten

Sekarang project sudah punya code, docs, API, Docker, dan multi-service stack.

Kalau repo dikerjakan tim, pertanyaannya berubah:

> “Gimana caranya kita tahu satu perubahan aman sebelum masuk stable branch?”

Kita nggak mau quality bergantung pada contributor ingat checklist manual.

Di step ini kita baca GitHub Actions workflow **sebagai system**, bukan sebagai YAML yang harus dihafal.

---

## Goal

Setelah selesai kalian harus bisa menjelaskan:

- trigger workflow;
- workflow, job, step;
- branch policy;
- quality job;
- matrix Docker build;
- cache;
- concurrency;
- permissions;
- develop → main flow;
- Continuous Delivery ke GHCR;
- kenapa tested commit harus sama dengan published commit.

---

# 1. Lihat branch flow dulu

Repository policy:

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

Kenapa workflow ini penting sebelum baca CI?

Karena CI punya branch-policy job yang encode flow tersebut.

CI bukan hanya test code.

Dia juga verify contribution process.

---

# 2. Open ci.yml

File:

~~~text
.github/workflows/ci.yml
~~~

Jangan baca semua syntax.

Mulai atas.

~~~text
name
on
permissions
concurrency
jobs
~~~

Ini skeleton GitHub Actions workflow.

---

# 3. name

~~~text
CI
~~~

Simple.

Nama muncul di Actions UI dan workflow_run trigger CD.

Naming jelas membantu chaining automation.

---

# 4. on — trigger

CI jalan pada:

~~~text
push
pull_request
workflow_dispatch
~~~

Push branches include main, develop, dan branch pattern work.

Pull request focus main/develop.

workflow_dispatch berarti manual run tersedia.

Question:

> “Kenapa feature branch push juga run CI?”

Supaya developer dapat feedback sebelum PR.

---

# 5. permissions

CI:

~~~text
contents: read
~~~

Kenapa read only?

Quality job tidak perlu write repo/package.

Least privilege.

Kalau workflow tidak butuh write, jangan kasih write.

---

# 6. concurrency

Config:

~~~text
group: ci-...
cancel-in-progress: true
~~~

Scenario:

~~~text
push commit A
↓
CI A running

push commit B 30 sec later
↓
CI B starts
~~~

CI A sudah obsolete untuk latest branch state.

Cancel old run menghemat runner.

---

# 7. Job 1 — Branch policy

Job hanya pada pull_request.

Dia baca:

~~~text
BASE_BRANCH
HEAD_BRANCH
~~~

Rules:

~~~text
to main
→ head must be develop

to develop
→ head must be feat/*, fix/*, docs/*, chore/*
~~~

Coba scenario.

### feat/new-api → develop

~~~text
✅
~~~

### develop → main

~~~text
✅
~~~

### feat/new-api → main

~~~text
❌
~~~

Process-as-code.

---

# 8. Kenapa branch policy CI belum sama dengan branch protection?

CI bisa fail.

Tapi platform permission menentukan apakah merge benar-benar blocked/bypass-able.

GitHub Ruleset/Branch Protection idealnya enforce:

- require PR;
- require checks;
- restrict direct push.

Jadi:

~~~text
CI policy
→ machine-check expected flow

platform ruleset
→ governance enforcement
~~~

---

# 9. Job 2 — Python + docs quality

Flow:

~~~text
checkout
↓
install uv
↓
install Python
↓
uv sync --group docs
↓
Ruff
↓
pytest
↓
MkDocs strict build
~~~

Mari bedah.

---

# 10. Checkout

Runner GitHub fresh.

Dia belum punya repo.

Checkout ambil revision yang sedang diuji.

Ini basic tapi lineage-critical.

CI result attach ke exact commit.

---

# 11. setup-uv

Workflow pin version:

~~~text
0.12.15
~~~

Kenapa pin tool version?

Supaya behavior CI tidak berubah random hanya karena action/tool latest release.

Dependencies/tooling juga bagian reproducibility.

---

# 12. uv python install + sync

Runner install Python sesuai project.

Lalu dependency sync.

Fresh runner useful karena expose hidden dependency.

Kalau local code cuma works karena package global yang lupa dicatat, CI bisa fail.

Itu good failure.

---

# 13. Ruff

~~~bash
uv run ruff check src api scripts tests
~~~

Ruff catch style/static issue.

Kita pernah benar-benar kena import ordering issue saat audit.

Itu contoh CI memberi feedback real, bukan decorative.

---

# 14. pytest

~~~bash
uv run pytest -q
~~~

Behavior test.

Kalau feature leakage regression atau API schema issue, test seharusnya catch known failure mode.

CI green memberi confidence, bukan mathematical proof zero bugs.

---

# 15. MkDocs strict build

~~~bash
uv run --group docs mkdocs build --strict
~~~

Kenapa docs masuk quality?

Karena workshop docs adalah product.

Broken navigation bisa merusak participant experience sama seperti code bug merusak API.

Strict build memaksa warning tertentu jadi failure.

---

# 16. Job 3 — Docker build matrix

Matrix target:

~~~text
api
mlflow
airflow
~~~

Same job template dijalankan per target.

Kenapa matrix?

Tanpa matrix YAML akan duplicate.

~~~text
job api
job mlflow
job airflow
~~~

Matrix lebih maintainable.

---

# 17. fail-fast false

Matrix punya:

~~~text
fail-fast: false
~~~

Kalau API image fail, MLflow/Airflow builds tetap boleh selesai.

Kenapa useful?

Kita dapat full picture:

~~~text
api ❌
mlflow ✅
airflow ✅
~~~

daripada first failure cancel semua.

Debugging lebih informative.

---

# 18. Docker Compose config validation

~~~bash
docker compose config --quiet
~~~

Ini catch invalid Compose config sebelum runtime.

Python tests tidak tahu YAML networking/volume config valid atau tidak.

Different artifact, different check.

---

# 19. Docker Buildx + cache

Image build pakai GitHub Actions cache.

Cache scope per target.

Kenapa?

API layer cache dan Airflow layer cache punya content pattern beda.

Cache mempercepat repeated build.

Tapi remember:

> Cache is optimization, not correctness dependency.

Clear cache harus tetap build.

---

# 20. Buat practice branch

Kita bisa demo dengan docs branch kecil.

~~~bash
git switch develop
git pull
git switch -c docs/workshop-practice
~~~

Edit satu harmless docs paragraph.

~~~bash
git add .
git commit -m "docs: practice contribution flow"
git push -u origin docs/workshop-practice
~~~

Open PR:

~~~text
docs/workshop-practice
↓
develop
~~~

---

# 21. Sebelum buka Actions, predict job result

Kalau perubahan hanya Markdown:

- branch policy?
- Python quality?
- docs build?
- Docker builds?

Semua tetap jalan sesuai current workflow.

Question:

> “Kenapa Docker build masih jalan padahal cuma docs?”

Current workflow simple dan conservative.

Future optimization bisa pakai path filters supaya docs-only PR skip expensive Docker builds.

Tradeoff:

~~~text
simple + safe
vs
optimized runner cost
~~~

---

# 22. Observe GitHub Actions UI

Buka workflow run.

Cari jobs:

~~~text
docs/workshop-practice
~~~

Klik quality job.

Read steps sequentially.

Jangan hanya lihat final green.

---

# 23. Controlled failure idea

Presenter bisa punya demo branch dengan intentional docs nav typo atau Ruff issue.

Goal:

> lihat quality gate fail sebelum merge.

Kemudian fix, push lagi, lihat CI green.

Ini membuat value automation tangible.

Jangan lakukan di main.

---

# 24. Develop → main

Setelah feature/docs PR squash merged ke develop dan develop green:

~~~text
develop
↓ PR
main
~~~

Branch policy menerima hanya develop ke main.

Main = stable release.

---

# 25. Open cd.yml

CD trigger:

~~~text
workflow_run
→ CI completed
~~~

Tapi publish job punya condition.

Dia hanya publish kalau:

~~~text
CI conclusion = success
event = push
head branch = main
~~~

Kenapa tidak PR?

Karena PR candidate belum stable release.

---

# 26. Checkout tested commit

CD checkout:

~~~text
workflow_run.head_sha
~~~

Ini sangat important.

CI test SHA A.

CD build SHA A.

Bukan random current latest.

Tested = published.

---

# 27. Login GHCR

Workflow pakai:

~~~text
GITHUB_TOKEN
~~~

dan permission:

~~~text
packages: write
~~~

No personal password committed.

---

# 28. Metadata tags

Docker metadata action produce:

~~~text
sha-<commit>
latest
~~~

SHA untuk traceability.

latest convenience pointer.

Coba answer:

> “Kalau mau rollback deterministic, pilih yang mana?”

SHA.

---

# 29. Build and push

Per target:

~~~text
api
mlflow
airflow
~~~

Build exact Dockerfile target lalu push tags ke GHCR.

Sekarang container registry punya deployable artifact.

---

# 30. Kenapa belum SSH/Kubernetes deploy?

Karena workshop belum punya real production target.

Tambahkan fake deploy command akan membuat peserta mengira deployment selesai hanya dengan satu baris.

Real deployment needs:

- credentials;
- network;
- TLS;
- rollout;
- health;
- rollback;
- scaling;
- secrets.

Kita berhenti jujur di Continuous Delivery.

---

# 31. Application release vs model release

Setelah CI/CD, ingat ada dua lifecycle.

~~~text
GitHub Actions
→ application artifact

MLflow Registry
→ model artifact
~~~

Main image bisa tetap sama sementara champion berubah.

Atau code image berubah sementara champion tetap.

Ini decoupling yang penting.

---

# 32. Mini scenarios

### Scenario A

pytest fail.

Apakah image publish?

No, CI tidak success.

### Scenario B

PR green tapi belum merge main.

Publish latest?

No.

### Scenario C

main push CI success.

Publish?

Yes.

### Scenario D

champion alias berubah tanpa code commit.

Apakah GitHub Actions harus build image?

Tidak necessarily.

Model lifecycle independent.

---

# Checkpoint

1. Workflow/job/step beda apa?
2. Trigger CI apa saja?
3. Branch policy rules?
4. CI policy dan branch protection beda apa?
5. Fresh runner kenapa useful?
6. Ruff, pytest, MkDocs, Docker masing-masing test layer apa?
7. Matrix build solve apa?
8. fail-fast false memberi benefit apa?
9. Cache role-nya apa?
10. develop → main kenapa separate?
11. CD condition publish kapan?
12. Kenapa checkout tested SHA?
13. latest vs SHA tag?
14. Kenapa workshop berhenti di Delivery?
15. Application release dan model release beda apa?

Kalau kalian bisa baca workflow dari event sampai artifact dan explain why, GitHub Actions nggak lagi kelihatan seperti YAML ritual.
