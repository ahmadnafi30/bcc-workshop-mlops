# Step 0 — Setup

## Goal

At the end of this step:

- Python 3.11 is available through uv,
- project dependencies are installed,
- tests can run,
- you understand the main repository folders.

Do not download the taxi dataset yet. First make sure the project itself is healthy.

## 1. Clone the repository

~~~bash
git clone https://github.com/ahmadnafi30/bcc-workshop-mlops.git
cd bcc-workshop-mlops
~~~

If the repository is private, GitHub may ask you to authenticate.

## 2. Install uv

Follow the official uv installation method for your operating system.

Verify:

~~~bash
uv --version
~~~

## 3. Sync the environment

~~~bash
uv sync
~~~

What happens conceptually:

~~~text
pyproject.toml
      ↓
uv resolves dependencies
      ↓
Python environment in .venv
      ↓
project package installed
~~~

You do not need to manually activate the virtual environment for workshop commands.

## 4. Verify Python

~~~bash
uv run python --version
~~~

Expected family:

~~~text
Python 3.11.x
~~~

The repository intentionally targets Python 3.11 for a predictable workshop environment.

## 5. Run the setup doctor

~~~bash
uv run python scripts/doctor.py
~~~

The doctor checks basic Python imports, project structure, and whether useful local commands such as Docker are discoverable.

A missing Docker command does not block the early ML steps. It matters later during containerization.

## 6. Run tests

~~~bash
uv run pytest
~~~

Why run tests before touching anything?

Because we want a known-good starting point.

If tests already fail before you change code, later debugging becomes ambiguous.

## 7. Optional: start the documentation

~~~bash
uv sync --group docs
uv run --group docs mkdocs serve
~~~

Open:

~~~text
http://127.0.0.1:8000
~~~

Keep the docs open during the workshop.

## Windows note

The core Python flow works with uv.

For the Docker + Airflow parts, WSL2 is usually the smoother learning environment on Windows.

The important thing is consistency: do not mix several Python installations and environments without knowing which one is active.

## Repository orientation

Before continuing, look at:

~~~text
scripts/
src/
dags/
api/
tests/
~~~

Remember:

~~~text
scripts
→ commands humans run

src
→ reusable logic

dags
→ workflow definitions

api
→ HTTP interface

tests
→ automated checks
~~~

## Checkpoint

You are ready when:

~~~text
uv run python --version
→ 3.11.x

uv run pytest
→ pass
~~~

Next: download and understand the data.
