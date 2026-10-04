# Project Setup with uv

Project ini pakai **uv** sebagai default tool buat Python environment dan dependency management.

Tujuannya simpel: peserta nggak perlu bikin virtual environment manual lalu install dependency satu-satu.

## Setup pertama

Pastikan uv sudah terinstall, lalu dari root repository:

```bash
uv sync
```

Command ini bakal:

```text
baca pyproject.toml
        ↓
pilih Python yang sesuai
        ↓
buat .venv
        ↓
resolve dependency
        ↓
install project + dev dependency
```

Project punya file:

```text
.python-version
```

yang kita set ke Python 3.11 supaya environment workshop lebih konsisten.

## Jalanin command

Kita pakai pola:

```bash
uv run <command>
```

Contoh:

```bash
uv run pytest
uv run python scripts/bootstrap_data.py
uv run mlflow server
```

Jadi kita nggak wajib activate environment dulu.

Kalau memang mau activate manual:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

## Tambah dependency

Kalau nanti ada dependency baru:

```bash
uv add <package>
```

Untuk dev dependency:

```bash
uv add --dev <package>
```

uv bakal update `pyproject.toml` dan lock file.

## Tentang uv.lock

Lock file penting karena dua orang yang menjalankan workshop seharusnya dapat dependency version yang sama.

Di environment ini kita belum generate `uv.lock` langsung dari repository karena dependency resolution tetap butuh akses package index. Begitu project dijalankan di laptop yang punya internet:

```bash
uv sync
```

uv akan generate lock file.

Setelah sudah dites:

```bash
git add uv.lock
git commit -m "chore: lock Python dependencies"
```

Jadi flow setup peserta nanti cukup:

```bash
git clone ...
cd bcc-workshop-mlops
uv sync
```

lalu project siap dipakai.


## Airflow environment

Airflow sengaja ditaruh di dependency group terpisah karena dependency-nya jauh lebih besar dibanding core ML project.

Untuk install core project + Airflow:

```bash
uv sync --group airflow
```

Jalankan Airflow dengan:

```bash
uv run --group airflow python scripts/start_airflow.py
```

Kalau mau cek DAG dari CLI:

```bash
uv run --group airflow airflow dags list
```

Di Windows, jalankan bagian Airflow lewat WSL2. Core Python project tetap bisa dipakai seperti biasa dari environment lain yang didukung uv.
