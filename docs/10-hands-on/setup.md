# Step 0 — Setup: Biar Semua Mulai dari Environment yang Sama

Hi peers, sebelum kita download data gigabytes, start Airflow, atau build Docker image, kita pastikan dulu environment basic-nya aman.

Ini kelihatannya boring, tapi setup yang nggak konsisten biasanya jadi sumber drama paling besar di workshop.

> “Kak, punya saya sklearn-nya beda.”

> “Kak, Python saya 3.13.”

> “Kak, command-nya masuk environment lain.”

Jadi Step 0 ini justru penting.

---

# Target step ini

Setelah selesai, kalian harus punya:

~~~text
Python 3.11
uv environment
project dependencies
pytest working
basic repo understanding
~~~

Docker belum wajib fully working di step ini. Nanti masuk section Docker baru kita strict check.

---

# 1. Clone repository

~~~bash
git clone https://github.com/ahmadnafi30/bcc-workshop-mlops.git
cd bcc-workshop-mlops
~~~

Coba setelah masuk folder, lihat:

~~~bash
ls
~~~

atau di Windows:

~~~powershell
dir
~~~

Kalian harus melihat file/folder seperti:

~~~text
api/
dags/
docs/
scripts/
src/
tests/
pyproject.toml
docker-compose.yml
dvc.yaml
~~~

Kalau kalian belum tahu semua folder buat apa, santai. Nanti satu-satu.

---

# 2. Check uv

~~~bash
uv --version
~~~

Kalau command belum ada, install uv sesuai official installation instruction untuk OS kalian.

Kenapa workshop nggak pakai plain pip saja?

Karena kita pengen semua dependency masuk project definition dan command jalan dari consistent environment.

---

# 3. Sync dependencies

~~~bash
uv sync
~~~

Saat command ini jalan, jangan cuma tunggu selesai.

Coba pahami apa yang sedang terjadi.

~~~text
pyproject.toml
      ↓
uv membaca dependency
      ↓
prepare Python environment
      ↓
install project + dev packages
~~~

Environment local biasanya berada di:

~~~text
.venv/
~~~

Folder itu ignored dari Git.

Kenapa?

Karena environment hasil install nggak perlu di-commit.

Yang di-commit adalah recipe-nya: pyproject.toml.

---

# 4. Check Python version

~~~bash
uv run python --version
~~~

Expected:

~~~text
Python 3.11.x
~~~

Kalau bukan 3.11, stop sebentar.

Jangan lanjut dengan asumsi:

> “Ah paling aman.”

Semakin ke Airflow, version mismatch makin mungkin bikin dependency issue.

---

# 5. Run doctor

~~~bash
uv run python scripts/doctor.py
~~~

Doctor check beberapa hal:

~~~text
Python 3.11
pandas import
sklearn import
DVC import
MLflow import
FastAPI import
Prometheus client
Docker CLI
~~~

Kalau Docker belum ada, early workshop masih bisa lanjut.

Tapi catat bahwa Step 7 nanti butuh Docker.

---

# 6. Run tests

~~~bash
uv run pytest
~~~

Kenapa tests dijalankan sekarang, sebelum kita ubah apa-apa?

Karena kita mau punya baseline:

~~~text
fresh clone
→ tests green
~~~

Nanti kalau setelah change tests fail, kita tahu failure kemungkinan dari perubahan kita.

Kalau dari awal sudah fail, debugging jadi ambiguous.

---

# 7. Coba lihat struktur project

Sekarang kita orientasi.

## src/

~~~text
src/
~~~

Reusable logic.

Kalau ada logic feature engineering yang ingin dipakai script, Airflow, dan test, sebaiknya hidup di sini.

## scripts/

~~~text
scripts/
~~~

Human-friendly entry point.

Contoh:

~~~bash
uv run python scripts/build_features.py
~~~

## dags/

~~~text
dags/
~~~

Airflow orchestration definition.

## api/

~~~text
api/
~~~

HTTP layer.

## tests/

~~~text
tests/
~~~

Automated checks.

---

# Satu rule yang enak diingat

~~~text
src/
HOW

scripts/
RUN THIS MANUALLY

dags/
WHEN + IN WHAT ORDER

api/
HOW OTHER APPS TALK TO THE MODEL
~~~

Nanti rule ini sering kita pakai.

---

# 8. Optional: run docs locally

Install docs group:

~~~bash
uv sync --group docs
~~~

Start:

~~~bash
uv run --group docs mkdocs serve
~~~

Open:

~~~text
http://127.0.0.1:8000
~~~

Kalau kalian self-learning, recommended banget keep docs tab open.

---

# Mini challenge

Sebelum lanjut, coba jawab tanpa lihat section atas:

> Kalau saya punya function aggregate demand yang dipakai script dan Airflow, sebaiknya logic intinya tinggal di scripts/, dags/, atau src/?

Jawaban:

~~~text
src/
~~~

Script dan DAG cukup call function-nya.

Kalau reasoning ini sudah masuk, structure repo mulai kebaca.

---

# Common issues

## uv command not found

uv belum installed atau PATH belum refresh.

## Python bukan 3.11

Pastikan uv/project Python resolution benar.

## pytest missing module

Coba:

~~~bash
uv sync
~~~

lagi dan pastikan kalian run:

~~~bash
uv run pytest
~~~

bukan pytest dari global environment.

---

# Checkpoint

Kalian siap Step 1 kalau:

~~~text
uv run python --version
→ 3.11.x

uv run python scripts/doctor.py
→ core checks okay

uv run pytest
→ pass
~~~

Next kita mulai menyentuh real taxi data.
