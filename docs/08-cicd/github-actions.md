# GitHub Actions — CI/CD yang Jalan Karena Event di Repository

GitHub Actions itu automation platform yang attached ke GitHub repository.

Kalau Airflow reacts ke workflow/data lifecycle, GitHub Actions biasanya reacts ke:

~~~text
push
pull request
manual dispatch
workflow completion
~~~

Jadi trigger domain-nya beda.

---

## Workflow file

Stored di:

~~~text
.github/workflows/
~~~

Project:

~~~text
ci.yml
cd.yml
~~~

YAML-nya mungkin awalnya kelihatan intimidating.

Baca dari luar ke dalam.

~~~text
name
↓
on / trigger
↓
permissions
↓
jobs
↓
steps
~~~

Jangan langsung fokus ke expression syntax.

---

## CI trigger

Kita run CI di branch development/release paths.

Pull request juga trigger.

Tujuannya:

> Before integration, verify repository state.

---

## Job vs Step

Workflow punya jobs.

Job punya steps.

Contoh:

~~~text
Job: Python + docs quality

Step:
checkout
setup uv
install
ruff
pytest
mkdocs
~~~

Jobs bisa parallel.

Steps dalam satu job mostly sequential.

---

## Checkout

Runner adalah fresh machine.

Dia belum punya repo.

actions/checkout clone exact revision yang mau dites.

Fresh runner bagus karena membuktikan project nggak cuma works karena hidden local state.

---

## setup-uv

Install uv on runner.

Lalu Python environment disiapkan.

CI seharusnya follow setup yang mirip developer workflow.

Kalau local pakai uv tapi CI pakai random pip logic beda, divergence lebih gampang muncul.

---

## Ruff

Ruff check basic lint/import order.

Kenapa style masuk CI?

Karena consistency mengurangi noise review.

Reviewer fokus ke logic daripada import order.

---

## pytest

Test functional behavior.

Unit tests catch regressions di feature, serving, monitoring logic.

CI test bukan proof system perfect, tapi safety net.

---

## MkDocs strict build

Docs adalah workshop product.

Strict build catch:

- invalid nav,
- missing page,
- rendering issue tertentu.

Kalau docs broken, workshop broken.

Jadi docs punya quality gate sama seperti code.

---

## Docker matrix

Kita build:

~~~text
api
mlflow
airflow
~~~

Matrix artinya same job template executed dengan target berbeda.

Daripada copy YAML tiga kali.

Benefit:

- less duplication,
- parallel execution,
- consistent logic.

---

## Docker cache

Build can reuse cache.

Tapi workflow harus tetap correct tanpa cache.

Cache = performance optimization.

Bukan dependency correctness.

---

## Concurrency

Kalau push commit A lalu cepat push B, CI A bisa dibatalkan.

Kenapa?

A sudah obsolete untuk branch latest.

Runner time bisa dipakai B.

---

## CD trigger

Container Delivery menunggu CI success di main.

Ini nice property:

~~~text
not every push
↓
only verified main revision
↓
publish image
~~~

---

## GITHUB_TOKEN

Workflow butuh auth ke GHCR.

GitHub provide scoped token.

Permission:

~~~text
packages: write
~~~

Kenapa bukan personal password hard-coded?

Credential di repo = disaster.

Use secret/token mechanism.

---

## Branch policy job

Project kita encode expected flow:

~~~text
docs/* → develop
feat/* → develop
fix/* → develop

develop → main
~~~

Kalau direction salah, CI fail.

Ini process-as-code.

---

## PR checks vs branch protection

CI check bisa fail, tapi kalau repository admin masih allow merge anyway, governance belum complete.

Ideal production setup juga enable GitHub ruleset/branch protection:

- require PR,
- require checks,
- restrict direct push.

Workshop connector tidak necessarily manage admin rules, tapi concept harus dipahami.

---

## Checkpoint

1. Workflow, job, step beda apa?
2. Kenapa runner fresh useful?
3. Kenapa docs build masuk CI?
4. Matrix dipakai buat apa?
5. GITHUB_TOKEN kenapa better than password?
6. CI branch policy beda apa dengan branch protection?
