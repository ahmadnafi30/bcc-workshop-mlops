# uv

## What is uv?

uv is the Python project and dependency manager used in this repository.

If you have used pip + venv before, uv roughly covers the same daily workflow, but with one project-oriented command flow.

Think of it as the person who prepares everyone's workshop laptop with the same recipe.

Without a project manager, setup often becomes:

~~~text
create venv
activate venv
install package A
install package B
forget package C
different laptop gets different result
~~~

With this project:

~~~bash
uv sync
~~~

is the main setup command.

## What does uv read?

The dependency definition lives in:

~~~text
pyproject.toml
~~~

That file says:

- project name,
- supported Python version,
- runtime dependencies,
- dev dependencies,
- Airflow dependency group,
- docs dependency group,
- pytest config,
- Ruff config.

## Why Python 3.11?

The repository has:

~~~text
.python-version
~~~

with Python 3.11.

We intentionally keep one workshop Python line because Airflow and the ML stack are easier to support when everyone uses the same runtime family.

## Core environment

~~~bash
uv sync
~~~

This installs the project plus the default dev group.

Then run commands through uv:

~~~bash
uv run pytest
uv run python scripts/bootstrap_data.py
~~~

You do not have to activate the virtual environment manually.

## Extra groups

Airflow is heavy, so it is separated:

~~~bash
uv sync --group airflow
~~~

Docs are also separate:

~~~bash
uv sync --group docs
~~~

Why groups?

Because a participant who only wants to run the model does not need every documentation and orchestration package immediately.

## Add a dependency

Runtime dependency:

~~~bash
uv add package-name
~~~

Dev-only dependency:

~~~bash
uv add --dev package-name
~~~

For this repository, dependency changes should be intentional and reviewed. Do not install a package locally and forget to record it in pyproject.toml.

## Common beginner confusion

### uv sync vs uv run

~~~text
uv sync
→ prepare environment

uv run ...
→ execute something inside that environment
~~~

### Do I need source .venv/bin/activate?

No.

You can, but the workshop commands use uv run so the instructions are consistent across machines.

### Why not pip install everything?

You can build a project that way, but the goal here is reproducible project setup, not a list of personal terminal history.

## Checkpoint

If these work, your base environment is healthy:

~~~bash
uv run python --version
uv run pytest
~~~

Python should be 3.11.x.
