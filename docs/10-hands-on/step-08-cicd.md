# Step 8 — GitHub Actions CI/CD

## Goal

Understand what happens after a repository change is pushed.

## Branch flow

~~~text
feat/* or fix/*
        ↓
      develop
        ↓
       main
~~~

## 1. Create a practice branch

~~~bash
git switch develop
git pull
git switch -c docs/workshop-practice
~~~

Make a harmless documentation change.

~~~bash
git add .
git commit -m "docs: practice contribution flow"
git push -u origin docs/workshop-practice
~~~

## 2. Open PR to develop

Correct direction:

~~~text
docs/workshop-practice
        ↓
      develop
~~~

CI should run automatically.

## 3. Observe CI

Jobs include:

~~~text
branch policy
Python + docs quality
Docker build - api
Docker build - mlflow
Docker build - airflow
~~~

Quality checks include Ruff, pytest, and a strict MkDocs build.

Docker builds catch packaging errors that unit tests cannot see.

## 4. Release direction

Stable release PR:

~~~text
develop
   ↓
 main
~~~

PRs directly from feature branches to main are rejected by the branch-policy job.

## 5. Delivery

Successful CI on main triggers container delivery:

~~~text
tested commit
   ↓
build images
   ↓
tag
   ↓
push to GHCR
~~~

## 6. Why no automatic cloud deploy?

This workshop has no real cloud production target. We stop honestly at a deployable container image instead of adding fake SSH or Kubernetes commands.

## Checkpoint

Explain the difference:

~~~text
Airflow
→ data/ML workflow automation

GitHub Actions
→ repository change automation
~~~
