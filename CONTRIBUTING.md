# Contributing to BCC Workshop — MLOps

Hi peers 👋

Repo ini dipakai sebagai project belajar sekaligus bahan workshop. Jadi perubahan yang masuk harus tetap **mudah dibaca pemula**, reproducible, dan nggak bikin flow workshop jadi lebih rumit tanpa alasan yang jelas.

## Branch flow

Kita pakai alur:

~~~text
feat/* atau fix/*
        ↓
      develop
        ↓
       main
~~~

Artinya:

- main adalah versi workshop yang paling stabil.
- develop adalah integration branch.
- feat/* buat fitur.
- fix/* buat bug.
- docs/* buat dokumentasi.
- chore/* buat maintenance.

Jangan develop feature langsung di main.

## Workflow

~~~bash
git switch develop
git pull
git switch -c feat/add-new-monitoring-panel
~~~

Sebelum PR:

~~~bash
uv sync --group docs
uv run ruff check src api scripts tests
uv run pytest
uv run --group docs mkdocs build --strict
~~~

Push dan PR ke develop.

Kalau develop stable, release via PR develop → main.

## Commit style

Pakai commit yang menjelaskan intent.

Good:

~~~text
feat: add prediction monitoring
fix: prevent future leakage in rolling features
docs: explain Airflow DAG for beginners
ci: validate docs and tests
~~~

Kurang membantu:

~~~text
update
fix again
changes
comment
~~~

## Coding style

Comment code sengaja casual dan beginner-friendly.

Function explanation pakai comment di atas def:

~~~python
# hitung metric regression yang dipakai buat compare model
def calculate_metrics(...):
    ...
~~~

Di dalam function, comment per logical block. Nggak perlu comment setiap literal line.

## Documentation style

Docs are part of the workshop product. A learner should always know **where they are, why this topic matters, what to do, and how to recognize success**.

### Page structure

- Keep exactly one H1 title per file. Use H2 for main sections and H3 for subsections. Do not skip heading levels.
- Start with a short paragraph that says who the page is for and what the reader will learn.
- For a how-to page, use this order: goal → prerequisites → numbered steps → expected result → troubleshooting → next page.
- For a concept page, explain the problem first, introduce the mental model, then connect it to this repository.
- Put optional deep dives under a clearly named section so a first-time reader can keep moving.

### Writing and examples

- Use conversational Indonesian with English technical terms where they are clearer. Explain a new term the first time it appears.
- Keep paragraphs focused on one idea. Prefer short steps over long command dumps.
- Label fenced code blocks with their language. Say which shell a command uses when Bash and PowerShell differ.
- After an important command, state what successful output or UI state should look like.
- Use tables for comparisons and short callouts for important tips, warnings, or expected behavior.
- Use emoji sparingly, and use relative links to pages inside this repository.

Example of the intended tone:

> “Sebelum Airflow, sebenarnya script kita sudah jalan. Problem-nya bukan Python nggak bisa execute command. Kita mulai butuh dependency, retry, dan execution history. Di sinilah orchestration berguna.”

Technical terms may remain in English:

~~~text
workflow
artifact
deployment
tracking
serving
ground truth
feature engineering
~~~


## Definition of done

Sebelum PR siap:

- tests lulus,
- Ruff lulus,
- docs strict build lulus,
- Docker Compose valid,
- flow docs diupdate kalau behavior berubah,
- tidak ada credential/generated data masuk Git,
- code masih explainable ke peserta newbie,
- docs punya cukup context, bukan hanya command list.
