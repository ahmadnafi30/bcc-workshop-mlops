# Step 8 — CI/CD: Let GitHub Check Our Work Automatically

Sampai sini project sudah cukup kompleks.

Kalau setiap perubahan harus ingat manual:

~~~text
ruff
pytest
mkdocs
docker build api
docker build mlflow
docker build airflow
~~~

lama-lama pasti ada yang lupa.

Jadi kita automate.

---

# Target step

Di step ini kita tidak coding feature besar.

Kita belajar workflow repository.

Kalian harus ngerti:

- branch strategy,
- Pull Request flow,
- CI jobs,
- container delivery.

---

# Branch flow

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

Main = stable.

Develop = integration.

Feature branch = work in progress.

---

# 1. Practice branch

Pastikan local develop up-to-date:

~~~bash
git switch develop
git pull
~~~

Create docs branch:

~~~bash
git switch -c docs/workshop-practice
~~~

Edit harmless docs text.

---

# 2. Commit

~~~bash
git add .
git commit -m "docs: practice contribution flow"
~~~

Message sudah menjelaskan intent.

Jangan:

~~~text
update
changes
fix
~~~

---

# 3. Push

~~~bash
git push -u origin docs/workshop-practice
~~~

Open GitHub.

Create PR:

~~~text
docs/workshop-practice
→
develop
~~~

---

# 4. Observe checks

CI akan mulai.

Jobs:

~~~text
Branch policy
Python + docs quality
Docker build - api
Docker build - mlflow
Docker build - airflow
~~~

---

# 5. Open quality job

Lihat step.

~~~text
checkout
setup uv
install Python
sync
Ruff
pytest
MkDocs strict
~~~

Kalian bisa lihat logs masing-masing.

Kalau Ruff fail, PR bukan “GitHub rusak”.

Ada exact code style issue.

---

# 6. Why branch policy?

Coba bayangin kalian accidentally PR:

~~~text
docs/workshop-practice
→
main
~~~

Policy job fail.

Karena main release harus lewat develop.

Ini membantu enforce team flow.

---

# 7. Docker matrix

Open Docker jobs.

Masing-masing target:

~~~text
api
mlflow
airflow
~~~

Parallel-ish independent build.

Matrix membuat YAML nggak duplicate full job.

---

# 8. Merge ke develop

Kalau PR checks green, feature dapat merge ke develop.

Biasanya squash merge useful buat clean history.

Jadi 10 WIP commits bisa masuk sebagai satu logical commit.

---

# 9. Release develop → main

Saat develop stable:

~~~text
develop
→
main
~~~

PR baru.

Branch policy memastikan source-nya develop.

---

# 10. Setelah main CI success

Container Delivery trigger.

Dia publish images ke GHCR.

Open Packages / workflow run.

Lihat:

~~~text
Publish api
Publish mlflow
Publish airflow
~~~

---

# 11. Tag

Image punya:

~~~text
latest
sha-...
~~~

Question:

> Kalau mau rollback exact application version, pakai latest atau SHA?

Better:

~~~text
SHA tag
~~~

karena immutable-ish exact revision reference.

---

# 12. Why no deployment server?

Karena workshop belum punya actual target infrastructure.

Jadi CD kita honest:

~~~text
tested
↓
packaged
↓
published
~~~

Tidak pretend production deployment.

---

# Mini challenge

> Kalau model champion berubah dari v1 ke v2 tapi API source code nggak berubah, apakah perlu build Docker image baru?

Tidak necessarily.

Model Registry alias selection independent dari application image.

Ini salah satu unique ML system concern.

---

# Checkpoint

Kalian harus bisa explain:

~~~text
Git branch lifecycle
vs
Airflow data lifecycle
vs
MLflow model lifecycle
~~~

Tiga lifecycle berbeda, tapi hidup dalam satu project.
