# GitHub Actions

## What is a workflow?

A GitHub Actions workflow is YAML stored under:

~~~text
.github/workflows/
~~~

It describes automated jobs triggered by repository events.

Our main files:

~~~text
ci.yml
cd.yml
~~~

## Event → workflow

Examples:

~~~text
push
→ CI

pull request
→ CI

successful CI on main
→ container delivery
~~~

This event-driven model is different from Airflow's data workflow orchestration.

## CI workflow

### Branch policy

For pull requests:

~~~text
feat/* → develop
develop → main
~~~

The CI job checks that PR direction matches the repository workflow.

This does not replace GitHub branch protection, but it makes the expected process visible and testable.

### Quality job

The quality job installs uv, prepares Python, and runs checks.

~~~text
Ruff
pytest
MkDocs build
~~~

Why build docs in CI?

Because broken documentation links or invalid navigation should be caught before workshop day.

### Docker matrix

We build multiple targets:

~~~text
api
mlflow
airflow
~~~

A matrix avoids copying the same job three times.

Conceptually:

~~~text
same build logic
×
different target
~~~

## Cache

GitHub Actions can reuse cached dependencies and Docker layers.

Caching is not correctness.

It is an optimization.

The workflow should still produce the same result when the cache is empty.

## Concurrency

Suppose you push commit A, then immediately push commit B.

CI for A may no longer be useful.

The workflow can cancel the older in-progress run for the same branch.

This saves runner time.

## Delivery workflow

The CD workflow waits for CI completion.

It only publishes when:

- CI succeeded,
- event came from a push,
- branch is main.

Pull requests do not publish release images.

## GITHUB_TOKEN

GitHub automatically provides a token to the workflow.

For GHCR publishing, the job requests:

~~~text
packages: write
~~~

This avoids storing a personal registry password in the repository.

## Secrets rule

Never commit credentials into workflow YAML.

Use GitHub Secrets or environment-based credentials for real secret values.

Our local demo configuration only contains non-secret defaults.

## Reading a workflow

When a YAML file looks overwhelming, read it in this order:

1. name;
2. trigger;
3. permissions;
4. jobs;
5. steps inside one job;
6. only then study expressions.

Do not try to understand the whole file at once.
