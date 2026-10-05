# Container Delivery

## What happens after CI succeeds?

On main:

~~~text
CI success
   ↓
Container Delivery
   ↓
build exact tested revision
   ↓
tag image
   ↓
push to GHCR
~~~

GHCR means GitHub Container Registry.

## Images

The workflow publishes separate images for:

~~~text
api
mlflow
airflow
~~~

Naming pattern:

~~~text
ghcr.io/<owner>/bcc-workshop-mlops-api
~~~

## Why tag with commit SHA?

A tag such as latest is convenient but movable.

~~~text
latest
today → commit A
tomorrow → commit B
~~~

A SHA-based tag points to a specific code revision.

That makes audit and rollback easier.

## Why rebuild in delivery?

CI proves:

> This image can be built.

Delivery creates the artifact we actually publish.

The delivery job checks out the exact commit that passed CI.

That preserves a clean chain:

~~~text
tested revision
=
published revision
~~~

## Why no automatic cloud deployment?

Because we do not have a real target environment in this workshop.

Adding fake SSH commands just to say “we have CD” would teach the wrong lesson.

Our boundary is honest:

~~~text
code
↓
verified
↓
container image
↓
GHCR
↓
ready for a deployment platform
~~~

A future extension could deploy that image to:

- a VPS,
- Cloud Run,
- ECS,
- Kubernetes,
- another container platform.

## Rollback mental model

If a bad application image is deployed, a platform can pull an older SHA-tagged image.

This is separate from **model rollback**, where MLflow champion can point to an older model version.

MLOps often has both:

~~~text
application version
and
model version
~~~

They need separate lineage.
