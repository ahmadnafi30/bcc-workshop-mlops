# Contributing to BCC Workshop — MLOps

Hi peers 👋

Repo ini dipakai sebagai project belajar sekaligus bahan workshop. Jadi perubahan yang masuk harus tetap **mudah dibaca pemula**, reproducible, dan nggak bikin flow workshop jadi lebih rumit tanpa alasan yang jelas.

## Branch flow

Kita pakai alur:

```text
feat/* atau fix/*
        ↓
      develop
        ↓
       main
```

Artinya:

- `main` adalah versi workshop yang paling stabil.
- `develop` adalah integration branch untuk perubahan yang sudah lolos review awal.
- `feat/*` dipakai buat fitur atau materi baru.
- `fix/*` dipakai buat bug fix.
- `docs/*` boleh dipakai kalau perubahan cuma dokumentasi.
- `chore/*` boleh dipakai buat maintenance.

Jangan bikin feature langsung di `main`.

## Contoh workflow

Mulai dari `develop`:

```bash
git switch develop
git pull

git switch -c feat/add-new-monitoring-panel
```

Setelah perubahan selesai:

```bash
uv sync --group docs
uv run ruff check src api scripts tests
uv run pytest
uv run --group docs mkdocs build --strict
```

Push branch:

```bash
git push -u origin feat/add-new-monitoring-panel
```

Lalu buat PR:

```text
feat/add-new-monitoring-panel
        ↓
      develop
```

Kalau develop sudah stabil dan mau dirilis:

```text
develop
   ↓
 main
```

## Commit style

Pakai commit yang menjelaskan intent, bukan aktivitas kecil.

Bagus:

```text
feat: add prediction monitoring
fix: prevent future leakage in rolling features
docs: explain Airflow DAG for beginners
ci: validate docs and tests
```

Kurang membantu:

```text
update
fix again
changes
comment
```

Satu commit idealnya mewakili satu logical change.

## Coding style

Project ini sengaja punya komentar yang santai dan beginner-friendly.

Untuk function:

```python
# hitung metric regression yang dipakai buat compare model
def calculate_metrics(...):
    ...
```

Kita menghindari docstring panjang di setiap function kalau komentar satu-dua baris sudah cukup.

Komentar di dalam function juga nggak perlu di setiap baris. Satu komentar cukup buat satu logical block.

## Definition of done

Sebelum PR dianggap siap:

- test lulus,
- Ruff lulus,
- docs build lulus,
- Docker Compose config valid,
- perubahan punya dokumentasi kalau mengubah workshop flow,
- nggak ada credential atau generated data yang ikut ke Git,
- code tetap bisa dijelaskan ke peserta yang baru belajar MLOps.
