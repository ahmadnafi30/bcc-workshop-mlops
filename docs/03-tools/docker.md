# Docker

## The problem

A project works on one laptop.

Another person runs it and gets:

~~~text
different Python
missing system package
different dependency
different command
~~~

Docker reduces that environmental variation by packaging an application runtime into an image.

## Analogy: shipping container

Before standard shipping containers, every type of cargo required different handling.

A container gives a standard outer shape.

Docker does something similar for applications:

~~~text
application
dependencies
runtime setup
start command
↓
image
~~~

The host still matters, but the application environment becomes much more predictable.

## Image vs container

This is one of the most common beginner questions.

~~~text
image
→ blueprint / template

container
→ running instance of that image
~~~

Analogy:

~~~text
class
→ image

object
→ container
~~~

Not technically identical, but useful.

## Dockerfile

Our file:

~~~text
docker/Dockerfile
~~~

describes how an image is built.

Important instructions include:

- FROM: base image,
- RUN: execute build command,
- COPY: copy files,
- ENV: set environment variable,
- WORKDIR: set working directory,
- CMD: default start command.

## Multi-stage build

We use one Dockerfile with multiple targets:

~~~text
base
├── api
├── mlflow
└── airflow
~~~

Why?

All services share the same core project, but they do not need identical runtime behavior.

### base

Contains:

- Python 3.11,
- uv,
- project package,
- core dependencies.

### api

Starts Uvicorn + FastAPI.

### mlflow

Starts MLflow tracking server.

### airflow

Adds the Airflow dependency group and starts Airflow.

## Why not one giant container?

You could run every process in one container, but service boundaries become harder to understand and manage.

Separate containers make the architecture clearer:

~~~text
API lifecycle
≠
MLflow lifecycle
≠
Airflow lifecycle
~~~

## Build manually

~~~bash
docker build -f docker/Dockerfile --target api -t bcc-mlops-api .
~~~

You normally use Docker Compose later, but manual build helps explain what Compose is automating.

## Bind mount vs volume

Two storage ideas appear in the project.

### Bind mount

Example:

~~~text
./data → /app/data
~~~

The host folder is directly visible inside the container.

Useful for workshop-generated files that we want to inspect from the host.

### Named volume

Example:

~~~text
mlflow-data
~~~

Docker manages the storage location.

Useful for service state.

## Non-root user

Our application image uses a non-root app user.

That is a healthier default than running every process as root.

It is not complete production hardening, but it introduces the idea that container security still matters.

## Common mistakes

### localhost confusion

Inside a container:

~~~text
localhost
→ this container
~~~

To reach another Compose service, use its service name.

### Rebuilding after code changes

A Docker image is a built artifact.

If source copied into the image changes, rebuild it.

### Assuming Docker solves everything

Docker helps runtime reproducibility.

It does not automatically solve:

- bad code,
- data leakage,
- model drift,
- insecure credentials,
- poor architecture.
