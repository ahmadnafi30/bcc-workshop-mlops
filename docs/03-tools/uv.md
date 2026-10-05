# uv — Biar Setup Python Project Nggak Jadi Ritual Manual

Sebelum ngomong MLOps yang jauh-jauh, kita butuh satu hal basic dulu: **environment yang konsisten**.

Karena workshop paling ngeselin itu bukan ketika model error.

Tapi ketika setengah peserta sudah masuk Airflow, setengah lagi masih:

> “Kak, pip saya kok beda?”

atau:

> “Python saya 3.13, aman nggak?”

Makanya kita pakai uv.

---

## Problem kalau setup manual

Flow klasik:

~~~text
python -m venv .venv
activate environment
pip install pandas
pip install sklearn
pip install mlflow
pip install ...
~~~

Bisa jalan.

Tapi ada problem:

- package bisa lupa dicatat,
- version bisa beda,
- command beda antar OS,
- environment global dan local bisa ketuker,
- reproducibility susah.

Project-oriented dependency manager bikin setup lebih predictable.

---

## uv itu apa?

Simplified:

> uv membantu manage Python version, environment, dependency, dan command execution dalam satu project workflow.

File utama yang dibaca:

~~~text
pyproject.toml
~~~

Di situ kita declare:

- project metadata,
- supported Python,
- runtime dependency,
- dev dependency,
- Airflow group,
- docs group,
- test config,
- lint config.

Jadi dependency bukan hasil memory dari terminal history.

Dia jadi bagian project.

---

## uv sync

Command utama:

~~~bash
uv sync
~~~

Mental model:

~~~text
pyproject.toml
↓
resolve dependency
↓
prepare .venv
↓
install project
↓
ready
~~~

Kalau project baru di-clone, ini salah satu command pertama.

---

## uv run

Setelah environment siap, kita execute command lewat:

~~~bash
uv run pytest
~~~

atau:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Kenapa enak?

Karena command otomatis dijalankan dalam project environment.

Kalian nggak wajib activate .venv manual.

---

## Dependency groups

Project kita tidak install semua hal super berat ke semua orang by default.

Ada beberapa group.

### Core + dev

~~~bash
uv sync
~~~

Enough buat:

- model code,
- tests,
- local development.

### Airflow

~~~bash
uv sync --group airflow
~~~

Airflow berat.

Nggak perlu ikut di base environment kalau peserta belum masuk orchestration section.

### Docs

~~~bash
uv sync --group docs
~~~

Untuk MkDocs Material.

---

## Kenapa group useful?

Bayangin semua dependency masuk satu bucket:

~~~text
FastAPI
Airflow
MkDocs
Jupyter
MLflow
test tools
lint tools
~~~

Environment jadi berat banget.

Group bikin installation lebih intentional.

---

## Python version

Repo target:

~~~text
Python 3.11
~~~

Kenapa nggak “yang terbaru aja”?

Karena ecosystem compatibility matters.

Airflow, MLflow, scikit-learn, dan dependency lain harus punya common compatible range.

“Newest Python” belum tentu “best workshop Python”.

Stable compatibility lebih penting.

---

## Doctor script

Kita punya:

~~~bash
uv run python scripts/doctor.py
~~~

Script ini check basic readiness:

- Python version,
- important imports,
- repository root,
- Docker CLI presence.

Kenapa ada doctor?

Karena error setup sebaiknya didetect sebelum workshop masuk ke feature engineering.

Fail early juga berlaku buat developer experience.

---

## Adding dependency

Kalau nanti project berkembang:

~~~bash
uv add package-name
~~~

Dev-only:

~~~bash
uv add --dev package-name
~~~

Tapi workshop contributor harus tetap tanya:

> “Dependency ini benar-benar dibutuhkan nggak?”

Setiap dependency menambah:

- install time,
- security surface,
- compatibility risk,
- image size.

Jadi jangan asal add library buat fungsi yang sebenarnya bisa dilakukan 5 lines standard library.

---

## uv bukan magic reproducibility

uv bantu environment consistency.

Tapi result ML tetap dipengaruhi:

~~~text
code
data
parameters
randomness
~~~

Environment reproducibility cuma satu layer.

Makanya kita masih butuh Git, DVC, MLflow, tests.

---

## Common mistakes

### Punya banyak Python installation

Command python bisa point ke version lain dari uv environment.

Biasakan:

~~~bash
uv run python --version
~~~

### pip install manual lalu lupa record

Local laptop works.

CI fails.

Karena dependency nggak ada di project definition.

### Install Airflow globally

Bisa bikin environment conflict yang membingungkan.

Lebih clean pakai project group.

---

## Checkpoint

1. uv sync buat apa?
2. uv run beda apa dengan sync?
3. Kenapa Airflow dipisah dependency group?
4. Kenapa workshop pin Python family?
5. Environment reproducibility solve bagian mana dari MLOps?
