# CI/CD Concepts

## Why automation after Git push?

Without CI, code quality depends on someone remembering:

~~~text
run tests
run lint
build docs
build Docker
~~~

Humans forget.

CI makes the verification step consistent.

## CI — Continuous Integration

Question:

> Is this change safe enough to integrate?

Our CI checks:

~~~text
branch policy
      ↓
dependency setup
      ↓
Ruff
      ↓
pytest
      ↓
MkDocs build
      ↓
Docker Compose validation
      ↓
Docker image build
~~~

CI does not automatically mean deployment.

It is primarily a quality gate.

## CD has two common meanings

### Continuous Delivery

~~~text
verified code
   ↓
build artifact
   ↓
publish artifact
   ↓
ready to deploy
~~~

### Continuous Deployment

~~~text
verified code
   ↓
publish
   ↓
automatically deploy to production
~~~

Our workshop uses **Continuous Delivery**.

We publish container images to GHCR but do not pretend we have a real cloud production target.

## Analogy: factory quality control

Code is a product moving through a factory.

CI is the inspection station.

CD is packaging the approved product and putting it in the warehouse.

Continuous Deployment would add:

> automatically ship it to the customer.

## Why Docker image is an artifact

An artifact is a built output of the software process.

Examples:

- Python wheel,
- binary,
- Docker image.

For this project, the deployable delivery artifact is the service container image.

## Why code and model lifecycle are separate

There are two kinds of change:

~~~text
code changed
→ CI/CD

model performance changed
→ monitoring/retraining
~~~

They can interact, but they are not the same trigger.

That distinction is important in MLOps.
