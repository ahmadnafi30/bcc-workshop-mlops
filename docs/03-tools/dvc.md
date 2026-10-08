# DVC: Versi Data dan Pipeline yang Bisa Diulang

Model yang dilatih hari ini perlu mempunyai jawaban untuk pertanyaan sederhana: **code, data, dan konfigurasi mana yang menghasilkan model ini?** Nama file saja belum cukup karena isi file dapat berubah.

## Git, DVC, dan MLflow berbagi pekerjaan

| Tool | Yang dicatat | Contoh di workshop |
|---|---|---|
| Git | Code dan metadata versi | Python, `params.json`, `dvc.yaml`, `dvc.lock` |
| DVC | Isi dataset/output dan hubungan pipeline | Training features dan snapshot CSV |
| MLflow | Eksperimen serta model | Parameters, MAE, artifacts, model versions |

CSV mudah dibaca, tetapi dataset besar tetap tidak perlu dimasukkan ke Git. Git menyimpan metadata kecil; DVC menyimpan isi file dalam cache dan remote.

## Dua cara menggunakan DVC

### 1. Melacak file langsung

```powershell
uv run dvc add data/simple_case/data.csv
```

DVC membuat `data.csv.dvc` yang menunjuk ke fingerprint isi CSV. Setelah CSV diubah dan disimpan, jalankan `dvc add` lagi untuk memperbarui metadata.

### 2. Menghasilkan file melalui pipeline

```powershell
uv run dvc repro create_training_snapshot
```

Project ini memakai dua stage:

```text
Daily demand CSV + params.json + Python code
                     ↓ build_training_features
data/features/training/taxi_demand_features.csv
                     ↓ create_training_snapshot
data/snapshots/training/taxi_demand_2025-01-26.csv
```

Output yang sudah tercatat di `dvc.yaml` **tidak perlu di-`dvc add` lagi**. Pipeline memakai `dvc.lock`; file mandiri memakai metadata `.dvc`.

## Baca dvc.yaml seperti kalimat

| Bagian | Pertanyaan yang dijawab |
|---|---|
| `cmd` | Command apa yang menghasilkan output? |
| `deps` | File/folder apa yang memengaruhi hasil? |
| `params` | Nilai konfigurasi mana yang perlu dipantau? |
| `outs` | File apa yang dihasilkan dan disimpan di cache? |

`params.json` menetapkan history awal dan cutoff snapshot. Dengan default Jan 1–26, features model-ready mulai Jan 8 karena lag satu minggu membutuhkan history. Training code kemudian membagi snapshot menjadi train Jan 8–21 dan validation Jan 22–26.

Snapshot bertanggal bukan otomatis file yang tidak dapat berubah. Catat metadata di Git dan simpan cache/remote agar isi versi lama tetap dapat dipulihkan.

## Mengapa dvc.lock memiliki banyak hash?

Setiap dependency dan output mempunyai fingerprint sendiri. DVC juga mencatat Python code karena perubahan cara mengolah data bisa menghasilkan output berbeda.

| Lokasi | Isi |
|---|---|
| `data.csv.dvc` | Metadata satu file yang di-`dvc add` |
| `dvc.lock` | Hasil resolusi command, params, deps, dan outs pipeline |
| `.dvc/cache/files/` | Isi output yang disimpan berdasarkan fingerprint |
| `.dvc/cache/runs/` | Catatan stage untuk memakai kembali output yang sudah tersedia |

Run cache DVC berbeda dari training run MLflow dan DAG run Airflow. Project juga menghitung SHA-256 snapshot untuk mencatat dataset identity di MLflow; lock DVC ini menggunakan MD5.

## Remote itu tempat menyimpan isi dataset

Remote DVC dapat berupa folder lokal, shared storage, atau layanan seperti S3. **Remote DVC berbeda dari remote GitHub.**

Untuk demo di Windows:

```powershell
uv run dvc remote list
# Jika belum ada remote demo, tambahkan:
uv run dvc remote add --local -d demo-local D:/bcc-dvc-storage
```

`--local` menyimpan konfigurasi khusus laptop di `.dvc/config.local`; `-d` memilih remote default. Jika `demo-local` sudah ada, pilih default dengan `uv run dvc remote default --local demo-local`.

| Command | Efek |
|---|---|
| `dvc push` | Upload isi cache yang diperlukan ke remote |
| `dvc pull` | Download isi yang diperlukan dan pulihkan output ke workspace |
| `dvc checkout` | Pulihkan output dari cache lokal sesuai metadata aktif |
| `git push` | Kirim code/metadata Git ke GitHub |

Folder lokal `D:/bcc-dvc-storage` cukup untuk simulasi. Untuk berbagi antarlaptop, gunakan storage yang dapat diakses semua peserta. Backend cloud mungkin memerlukan dependency tambahan serta credentials sesuai layanan.

## Apakah dvc pull memulihkan seluruh project?

Tidak. DVC memulihkan **output yang dilacak**. Pada pipeline ini, daily demand adalah dependency, bukan output yang diupload otomatis oleh stage snapshot. Untuk membangun ulang dari sumber, jalankan bootstrap dan history preparation; untuk memperoleh snapshot versi tertentu, gunakan metadata Git yang sesuai lalu `dvc pull`.

## Mulai praktik

- [Hands-on DVC: add, push, pull, restore, lalu pipeline repo](../10-hands-on/step-03-dvc.md)
- [CSV Data Flow: file mana yang dibaca setiap proses](../05-data-pipeline/csv-data-flow.md)
- [Airflow + DVC: UI dan orchestration](../05-data-pipeline/airflow-dvc-workshop.md)
