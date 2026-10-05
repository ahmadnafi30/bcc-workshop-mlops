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

Ini penting karena docs adalah bagian utama workshop.

Docs **jangan ditulis seperti API reference full-English yang kaku**.

Target tone:

- natural mix Indonesian + English technical terms,
- conversational tapi tetap technical,
- boleh panjang kalau memang memberi context,
- gunakan pertanyaan retoris,
- gunakan analogi kalau membantu,
- explain “why” sebelum “how”,
- selalu connect tool ke problem project,
- jangan terlalu banyak emoji,
- jangan terlalu banyak bullet tanpa penjelasan.

Contoh tone yang kita mau:

> “Sebelum Airflow, sebenarnya script kita sudah jalan. Problem-nya bukan Python nggak bisa execute command. Problem-nya kita mulai butuh dependency, retry, dan execution history. Nah, di sinilah orchestration mulai masuk.”

Bukan:

> “Airflow is a workflow orchestration platform. It uses DAGs.”

Technical term English tetap boleh dan justru sering lebih natural:

~~~text
workflow
artifact
deployment
tracking
serving
ground truth
feature engineering
~~~

Yang penting explanation-nya approachable.

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
