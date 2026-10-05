# Step 0 — Setup: Bikin Semua Orang Start dari Kondisi yang Sama

Hi peers 👋

Sebelum download dataset beberapa GB, sebelum buka Airflow, sebelum ngetes Docker, kita pastikan dulu environment dasar sehat.

Kenapa ini penting?

Karena kalau baseline environment belum jelas, setiap error berikutnya jadi ambiguous.

Misalnya training fail.

Apakah karena code?

Atau dependency belum ke-install?

Atau Python version salah?

Atau kalian ternyata pakai global environment?

Kita eliminate uncertainty dari awal.

---

## Goal step ini

Setelah selesai, kalian harus punya:

- repository berhasil di-clone,
- Python 3.11 tersedia lewat uv,
- core dependency ter-install,
- doctor script green,
- pytest bisa jalan,
- ngerti basic folder structure.

Belum perlu Docker jalan.

Belum perlu Airflow.

Kita build foundation dulu.

---

## 1. Clone repository

~~~bash
git clone https://github.com/ahmadnafi30/bcc-workshop-mlops.git
cd bcc-workshop-mlops
~~~

### Pause sebentar

Coba lihat:

~~~bash
ls
~~~

atau di Windows explorer.

Kalian akan lihat folder seperti:

~~~text
api
dags
data
docs
scripts
src
tests
~~~

Jangan dihafal.

Cukup ingat:

~~~text
src
→ reusable logic

scripts
→ command manusia

dags
→ workflow Airflow

api
→ HTTP interface

tests
→ safety net
~~~

Nanti tiap folder akan punya konteks.

---

## 2. Check uv

~~~bash
uv --version
~~~

Kalau command not found, install uv dulu sesuai OS.

Kenapa kita nggak pakai pip + venv manual?

Bisa sebenarnya.

Tapi workshop butuh satu workflow setup yang konsisten lintas peserta.

uv bikin dependency/project environment lebih predictable.

---

## 3. Sync environment

~~~bash
uv sync
~~~

### Sebelum run, coba tebak

Command ini kira-kira melakukan apa?

Bukan sekadar “install package”.

Mental model:

~~~text
read pyproject
↓
resolve dependency
↓
prepare .venv
↓
install project
↓
ready
~~~

### What just happened?

Coba check:

~~~bash
uv run python --version
~~~

Expected:

~~~text
Python 3.11.x
~~~

Kalau 3.11, good.

Kalau bukan, jangan lanjut dulu tanpa ngerti kenapa.

---

## 4. Doctor script

~~~bash
uv run python scripts/doctor.py
~~~

Doctor check beberapa requirement dasar.

Kalian mungkin lihat:

~~~text
[OK] Python 3.11
[OK] import pandas
[OK] import sklearn
...
~~~

Docker bisa jadi belum ready.

Itu nggak masalah untuk Step 0–6.

Doctor sengaja bedakan core requirement dengan tool yang baru dibutuhkan nanti.

---

## 5. Run tests

~~~bash
uv run pytest
~~~

Kenapa run tests sekarang, padahal kita belum coding?

Karena kita butuh **known-good starting point**.

Bayangin kalian langsung edit feature code, lalu test fail.

Kalau sebelumnya nggak pernah run test, kita nggak tahu:

> “Ini fail karena perubahan saya, atau repo dari awal sudah fail?”

Baseline test state menghilangkan ambiguity.

---

## 6. Optional: run docs locally

~~~bash
uv sync --group docs
uv run --group docs mkdocs serve --dev-addr 127.0.0.1:8002
~~~

Open:

~~~text
http://127.0.0.1:8002
~~~

Kalian bisa keep tab docs ini selama workshop.

Port 8002 dipakai agar docs tidak bentrok dengan prediction API di port 8000.

---

## 7. Explore pyproject.toml

Jangan skip ini.

Open:

~~~text
pyproject.toml
~~~

Cari:

- requires-python,
- dependencies,
- dependency-groups,
- pytest config,
- Ruff config.

Pertanyaan buat diri sendiri:

> “Kalau saya add package manual pakai pip tapi nggak update project definition, apa yang terjadi di CI?”

Jawaban:

CI fresh machine nggak tahu package personal kalian.

Makanya dependency harus jadi project metadata.

---

## 8. Mini challenge

Tanpa lihat docs, coba jawab:

### A

Kalau mau run script build_features.py, command mana lebih konsisten?

~~~text
python scripts/build_features.py
~~~

atau:

~~~text
uv run python scripts/build_features.py
~~~

Kenapa?

### B

Airflow belum terinstall setelah uv sync biasa.

Apakah repo broken?

No.

Airflow ada dependency group sendiri.

---

## Common issues

### uv command not found

Install uv.

### Python version nggak 3.11

Check project Python setup.

Jangan paksa global interpreter random.

### Import error setelah sync

Coba:

~~~bash
uv sync
~~~

lagi dan lihat error resolution.

### pytest fail

Read exact failing test.

Jangan langsung delete test. 😭

---

## Checkpoint

Sebelum lanjut, pastikan:

~~~bash
uv run python --version
uv run python scripts/doctor.py
uv run pytest
~~~

semuanya masuk akal.

Kalau iya, kita masuk Step 1 dan mulai main dengan data real.
