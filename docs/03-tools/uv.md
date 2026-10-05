# uv — Managing Our Python Environment

## Kenapa kita perlu bahas environment dulu?

Sebelum masuk MLflow, Airflow, atau Docker, ada problem yang jauh lebih basic:

> “Project ini sebenarnya jalan pakai Python versi berapa dan dependency apa saja?”

Kalau tiap peserta setup seperti ini:

~~~text
pip install pandas
pip install sklearn
pip install mlflow
pip install airflow
...
~~~

kemungkinan besar beberapa laptop akan punya versi package berbeda.

Terus muncul classic problem:

> “Di laptop saya bisa kak.”

😄

Makanya kita pakai **uv** buat manage project environment.

---

# uv itu apa?

Secara practical, uv membantu kita:

- manage Python environment,
- install dependencies,
- run command dalam project environment,
- manage dependency groups.

Kalau sebelumnya kalian familiar dengan:

~~~text
python -m venv
pip install
requirements.txt
~~~

uv meng-cover banyak workflow itu dalam satu project-oriented tool.

---

# File utama: pyproject.toml

Dependency project kita ditulis di:

~~~text
pyproject.toml
~~~

Di situ ada beberapa category.

## Runtime dependencies

Ini package yang memang dibutuhkan application.

Contoh:

~~~text
pandas
scikit-learn
mlflow
fastapi
dvc
prometheus-client
~~~

## Development dependencies

Contoh:

~~~text
pytest
ruff
jupyterlab
httpx
~~~

Ini mostly buat development dan testing.

## Airflow group

Airflow sengaja dipisah.

Kenapa?

Karena Airflow dependency cukup berat.

Kita nggak mau setiap participant yang cuma mau run basic model harus install seluruh Airflow stack dari awal.

Jadi:

~~~bash
uv sync --group airflow
~~~

baru install extra Airflow dependencies.

## Docs group

Docs juga punya group:

~~~bash
uv sync --group docs
~~~

yang install MkDocs Material.

---

# Command paling penting: uv sync

~~~bash
uv sync
~~~

Mental model:

~~~text
pyproject.toml
      ↓
resolve dependency
      ↓
create/update .venv
      ↓
install project
~~~

Kalau environment belum ada, dibuat.

Kalau dependency berubah, disinkronkan.

---

# uv run

Setelah environment siap, kita run command:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Apa bedanya dengan:

~~~bash
python scripts/bootstrap_data.py
~~~

Dengan uv run, kita explicitly run command di project environment yang sudah di-manage uv.

Jadi kita nggak terlalu bergantung ke shell activation state.

---

# Apakah masih perlu activate .venv?

Nggak wajib.

Kalian tetap bisa activate kalau nyaman.

Tapi docs workshop pakai:

~~~bash
uv run ...
~~~

supaya command lebih consistent di banyak environment.

---

# Kenapa Python 3.11?

Repo punya:

~~~text
.python-version
~~~

yang menunjuk Python 3.11.

Kenapa kita pin major/minor?

Karena ecosystem project kita cukup banyak:

- MLflow,
- Airflow,
- sklearn,
- FastAPI.

Semakin random Python version peserta, semakin besar kemungkinan compatibility issue.

Workshop bukan tempat ideal buat debug:

> “Package ini belum support Python X.Y terbaru.”

Jadi kita pilih environment yang controlled.

---

# Dependency group analogy

Coba bayangin kalian punya backpack.

Core dependency adalah barang yang selalu dibawa.

~~~text
wallet
phone
water
~~~

Airflow group seperti:

~~~text
camera equipment
~~~

Berat, dan cuma dibutuhkan kalau masuk sesi tertentu.

Docs group seperti:

~~~text
presentation equipment
~~~

Juga nggak dibutuhkan setiap saat.

Jadi group bikin environment lebih modular.

---

# Add dependency

Kalau nanti kalian develop project:

~~~bash
uv add package-name
~~~

Untuk dev-only:

~~~bash
uv add --dev package-name
~~~

Yang penting:

> Jangan install package lokal lalu lupa menambahkannya ke project definition.

Karena nanti hanya laptop kalian yang tahu dependency itu.

---

# Doctor script

Workshop punya helper:

~~~bash
uv run python scripts/doctor.py
~~~

Dia cek beberapa hal basic:

- Python version,
- essential imports,
- repo structure,
- Docker CLI availability.

Docker belum wajib untuk early stage.

Jadi kalau Docker missing, basic ML flow masih bisa dipelajari dulu.

---

# Common confusion

## uv sync vs uv run

~~~text
uv sync
→ prepare environment

uv run
→ execute command inside environment
~~~

## pyproject.toml vs uv environment

~~~text
pyproject.toml
→ desired project definition

.venv
→ installed environment state
~~~

## uv vs Docker

Mereka solve problem berbeda.

~~~text
uv
→ Python project environment

Docker
→ containerized runtime environment
~~~

Docker image kita bahkan pakai uv saat build.

---

# Quick checkpoint

Run:

~~~bash
uv run python --version
uv run python scripts/doctor.py
uv run pytest
~~~

Kalau semua core check aman, environment kalian siap.

Baru setelah itu kita masuk data pipeline.
