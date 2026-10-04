# Git Workflow

## Why more than main?

For a personal experiment, direct commits to main are convenient.

For collaborative work, we want a small safety boundary.

~~~text
feat/* or fix/*
        ↓
      develop
        ↓
       main
~~~

## Branch roles

### feat/* — workbench

This is where a feature is built and changed freely.

Example:

~~~text
feat/add-drift-dashboard
~~~

### develop — integration

Completed features meet here.

A PR into develop should pass tests, linting, docs build, and Docker validation.

### main — stable workshop release

Main is the version we are comfortable showing to participants.

A PR into main should come from develop.

## Normal workflow

~~~bash
git switch develop
git pull
git switch -c feat/my-feature
~~~

After coding:

~~~bash
git add .
git commit -m "feat: add my feature"
git push -u origin feat/my-feature
~~~

PR:

~~~text
feat/my-feature
      ↓
   develop
~~~

Release:

~~~text
develop
   ↓
 main
~~~

## Why not feat → main?

Because individually-correct changes can conflict when combined.

Develop gives us an integration point before stable release.

## CI policy

Allowed:

~~~text
feat/*  → develop
fix/*   → develop
docs/*  → develop
chore/* → develop

develop → main
~~~

The CI workflow checks PR direction.

Repository branch protection can be enabled in GitHub Settings for an even stricter setup.

## Commit messages

We use simple Conventional Commit-style prefixes:

| Prefix | Purpose |
| --- | --- |
| feat | functionality |
| fix | bug |
| docs | documentation |
| refactor | structure without behavior change |
| test | tests |
| ci | automation |
| chore | maintenance |

Prefer:

~~~text
feat: add model performance monitoring
~~~

over:

~~~text
update stuff
~~~

Readable history is part of maintainability.
