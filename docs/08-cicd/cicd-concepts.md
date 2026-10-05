# CI/CD — Biar Quality Nggak Bergantung ke “Jangan Lupa Run Test Ya”

Sekarang bayangin repo mulai dikerjakan beberapa orang.

Sebelum merge, harusnya:

- test,
- lint,
- docs build,
- Docker build.

Kalau process-nya:

> “Guys jangan lupa run test sebelum push.”

Ada satu masalah: manusia lupa. 😭

CI masuk buat bikin quality gate lebih konsisten.

---

## CI = Continuous Integration

CI menjawab:

> “Perubahan code ini aman nggak buat diintegrasikan?”

Project kita check:

~~~text
branch policy
↓
setup environment
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

Perhatikan: CI bukan cuma unit test.

Karena repository kita bukan cuma Python code.

Docs dan Docker juga bagian deliverable.

---

## Kenapa docs build masuk CI?

Workshop docs adalah product juga.

Kalau nav broken atau markdown extension error, workshop experience rusak.

Jadi docs failure sama valid-nya dengan code failure.

---

## Kenapa Docker build masuk CI?

Python test bisa green tapi Docker build fail.

Contoh:

~~~text
COPY path salah
dependency missing di image
Dockerfile syntax error
~~~

CI build image supaya packaging error ketahuan sebelum release.

---

## Branch workflow

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

Kenapa develop?

Supaya ada integration stage sebelum stable release.

Feature individually green belum tentu compatible dengan feature lain.

Develop jadi tempat mereka ketemu dulu.

---

## Branch policy

CI check PR direction.

Allowed:

~~~text
feat/* → develop
fix/* → develop
docs/* → develop
chore/* → develop

develop → main
~~~

Kenapa policy di CI?

Supaya workflow repository bukan cuma tulisan di README.

Ada automated guard.

Idealnya GitHub branch protection/ruleset juga dipasang.

---

## CD itu ambiguity

CD bisa berarti:

~~~text
Continuous Delivery
atau
Continuous Deployment
~~~

Workshop kita pakai **Continuous Delivery**.

Artinya:

~~~text
verified code
↓
build artifact
↓
publish artifact
↓
ready to deploy
~~~

Kita belum automatically deploy ke production cloud.

Kenapa?

Karena repo belum punya real production target.

Lebih jujur berhenti di GHCR daripada fake deploy command cuma supaya diagram terlihat lengkap.

---

## Artifact delivery

Container image adalah deployment artifact.

Kita publish:

~~~text
API image
MLflow image
Airflow image
~~~

ke GHCR.

---

## latest vs SHA tag

latest convenient.

Tapi movable.

~~~text
today latest = commit A
tomorrow latest = commit B
~~~

SHA tag identify exact revision.

Useful buat:

- audit,
- rollback,
- traceability.

---

## Code lifecycle vs model lifecycle

Ini salah satu concept MLOps yang subtle.

~~~text
new code
→ CI/CD

new data / performance degradation
→ retraining lifecycle
~~~

Model bisa berubah tanpa application code berubah.

Application code bisa berubah tanpa retrain model.

Jadi kita punya dua lifecycle yang related tapi tidak identical.

---

## Analogi factory

CI = quality inspection.

CD = packaging approved product dan taruh ke warehouse.

Continuous Deployment = warehouse langsung kirim ke customer automatically.

Workshop berhenti di warehouse.

---

## Checkpoint

1. CI solve problem apa?
2. Kenapa docs dan Docker ikut CI?
3. Develop branch buat apa?
4. Continuous Delivery beda apa dengan Deployment?
5. Kenapa SHA image tag useful?
6. Code lifecycle beda apa dengan model lifecycle?
