# Step 8 — CI/CD: Sekarang Kita Simulasikan Cara Kerja Team

Local project sudah works.

Sekarang pertanyaan:

> “Kalau ada orang ubah code, siapa yang memastikan semuanya masih sehat?”

Kita pakai GitHub workflow.

---

## Goal

Setelah step ini:

- ngerti branch flow,
- bisa baca CI run,
- ngerti setiap quality check,
- ngerti delivery ke GHCR,
- ngerti kenapa feature nggak langsung main.

---

## 1. Review branch flow

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

Question:

> “Kenapa nggak feature langsung main?”

Karena develop jadi integration zone.

---

## 2. Create practice docs branch

~~~bash
git switch develop
git pull
git switch -c docs/workshop-practice
~~~

Edit satu docs line harmless.

Commit:

~~~bash
git add .
git commit -m "docs: practice contribution flow"
git push -u origin docs/workshop-practice
~~~

---

## 3. Open PR to develop

Base:

~~~text
develop
~~~

Head:

~~~text
docs/workshop-practice
~~~

Jangan ke main.

Lihat CI start.

---

## 4. Open Branch Policy job

Apa yang dia check?

PR direction.

Coba imagine kalau base main tapi head docs/workshop-practice.

Expected fail.

Ini governance process encoded di CI.

---

## 5. Open Python + docs quality

Steps:

~~~text
checkout
setup uv
sync
ruff
pytest
mkdocs strict
~~~

Click satu step.

Read log.

CI bukan black box.

---

## 6. Open Docker build jobs

Ada matrix:

~~~text
api
mlflow
airflow
~~~

Pertanyaan:

> “Kenapa tests green belum cukup?”

Karena packaging bisa fail.

Docker build is separate validation.

---

## 7. Merge to develop

Kalau practice, kalian nggak harus benar-benar merge kalau repo workshop shared.

Presenter bisa demo dari existing PR.

Concept:

~~~text
feature
↓
develop
↓
integration CI
~~~

---

## 8. Release PR

Stable release:

~~~text
develop
↓
main
~~~

Branch policy expect direction ini.

---

## 9. After main CI

Container Delivery triggers.

Open workflow.

Observe jobs:

~~~text
Publish api
Publish mlflow
Publish airflow
~~~

---

## 10. GHCR

Published image punya tags.

Cari:

~~~text
latest
sha-...
~~~

Question:

> “Untuk exact rollback, kalian lebih percaya latest atau SHA?”

SHA.

---

## Mini challenge

Kalau model champion berubah tapi code nggak berubah, apakah GitHub Actions necessarily harus run?

Tidak.

Model lifecycle bisa move lewat Registry.

Ini perbedaan code lifecycle vs model lifecycle.

---

## Checkpoint

1. Kenapa develop ada?
2. Branch policy check apa?
3. Ruff vs pytest?
4. Kenapa MkDocs build di CI?
5. Docker matrix buat apa?
6. GHCR role?
7. latest vs SHA?
