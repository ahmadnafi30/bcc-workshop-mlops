# MLflow hands-on: Compare Three Experiments

Zora sudah punya model yang mengalahkan baseline. Sekarang ia perlu menjawab:

> Which configuration should we choose, and what evidence supports that choice?

Di latihan ini kita mencatat **parameters, metrics, artifacts, dan data lineage**, membandingkan tiga konfigurasi, lalu membaca alasan pemilihan model. Latihan mengikuti tujuan materi Eksperimentasi ML: bukan sekadar mengulang training dengan konfigurasi yang sama.

## 1. Prepare the server and data

Jalankan semua command dari folder repository. Snapshot training harus sudah dibuat melalui [Step 3: DVC](../10-hands-on/step-03-dvc.md).

~~~powershell
cd D:\bcc-workshop-mlops
docker compose up -d mlflow
$env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
~~~

| Command | Fungsinya |
| --- | --- |
| `cd D:\bcc-workshop-mlops` | Menentukan folder kerja untuk script dan Compose |
| `docker compose up -d mlflow` | Menyalakan MLflow di background dengan state `.mlflow` yang tersimpan |
| `$env:MLFLOW_TRACKING_URI = ...` | Mengarahkan training dari terminal ini ke server yang akan dilihat di UI |

Kalau Docker Desktop belum berjalan, buka Docker Desktop terlebih dahulu. Untuk mode Python lokal, gunakan command berikut di terminal terpisah dan biarkan terminal tersebut berjalan:

~~~powershell
uv run python scripts/start_mlflow.py
~~~

Gunakan salah satu server pada port 5000. Buka [MLflow UI](http://localhost:5000). Server dan folder data saja belum menghasilkan experiment; training yang membuat run.

## 2. Run the three configurations

~~~powershell
uv run python scripts/train_with_mlflow.py --search
~~~

`--search` menjalankan satu baseline dan tiga kandidat **secara berurutan**, dengan maksimum dua thread CPU untuk operasi model. Kita tidak menjalankan grid search besar.

| Configuration | learning_rate | max_iter | max_leaf_nodes | l2_regularization | Pertanyaan eksperimen |
| --- | ---: | ---: | ---: | ---: | --- |
| compact | 0.10 | 100 | 15 | 1.0 | Apakah model lebih kecil cukup akurat? |
| balanced | 0.05 | 200 | 31 | 0.1 | Bagaimana performa konfigurasi workshop awal? |
| slow-learning | 0.03 | 300 | 31 | 1.0 | Apakah pembelajaran lebih lambat membantu validation? |

Semua kandidat memakai `loss=poisson`, `random_state=42`, feature yang sama, snapshot yang sama, dan split waktu yang sama. `max_iter` adalah batas iterasi; lihat `fitted_iterations` untuk jumlah aktual. Beberapa parameter berubah bersama, jadi ini membandingkan konfigurasi, bukan membuktikan efek satu parameter secara terpisah.

**Expected output:** satu parent run search, satu child baseline, dan tiga child model. Total lima run baru. Parent menyimpan laporan; child menyimpan bukti setiap percobaan. Banyak run lama tidak berarti ada banyak variasi hyperparameter.

Output terminal menyediakan `parent_run_id`, `best_run_id`, `best_config`, metric, dan `report_dir`. Hasil nyata bergantung pada data, jadi jangan memakai angka contoh sebagai hasil latihanmu.

## 3. Read the UI step by step

1. Di kiri atas, pilih **Model training**, lalu experiment **taxi-demand-forecasting** dan halaman **Runs**. Mode **GenAI** mempunyai menu berbeda; latihan ini memakai model training.
2. Cari parent **hgb-hyperparameter-search** terbaru. Expand child runs jika UI menyediakan tampilan nested.
3. Centang tiga child model, lalu pilih **Compare**. Tambahkan baseline untuk konteks error.
4. Tampilkan parameter `learning_rate`, `max_iter`, `max_leaf_nodes`, dan `l2_regularization`.
5. Bandingkan metric `mae`, `rmse`, `fit_seconds`, dan `fitted_iterations`. Jika tabel Runs belum menampilkan metric, gunakan **Columns** untuk menambahkan kolomnya. Di detail run, nilainya juga tersedia pada **Overview** atau **Model metrics**.
6. Pastikan `dataset_sha256`, `validation_start`, dan `validation_end` sama. Tag `comparison_id` menghubungkan run dalam satu latihan.
7. Buka run kandidat untuk membaca dataset inputs pada bagian **Datasets/Inputs**, sesuai versi UI. Context `training` dan `validation` menjelaskan peran data.
8. Buka parent run, lalu **Artifacts**, dan lihat folder `comparison`.

| UI / field | Apa yang perlu dijelaskan ke peserta |
| --- | --- |
| Parameters | Konfigurasi yang digunakan; efektif estimator parameters juga dicatat |
| Metrics: MAE | Rata-rata besar error pickup count; lebih kecil lebih baik pada evaluation yang sama |
| Metrics: RMSE | Lebih sensitif terhadap kesalahan besar |
| Metrics: fit_seconds | Waktu fit saja; bukan benchmark latency API |
| Duration | Waktu run mencakup metadata, training, evaluation, dan artifact logging |
| Tags | Konteks seperti config name, comparison ID, Git commit, dan status dirty |
| Datasets / Inputs | Schema, digest, dan context train/validation; source mengarah ke snapshot |
| Artifacts | Model, input example, dependencies, hasil evaluasi, dan laporan |

Nama tab dan lokasi tombol dapat berubah antarversi MLflow. Fokus pada run, parameters, metrics, inputs, artifacts, dan Models. Grafik loss per epoch bukan output wajib untuk model ini; kita mencatat evaluasi akhir dan jumlah iterasi aktual.

## 4. Inspect the evidence

### Artifacts pada setiap child model

| Artifact | Isi dan kegunaan |
| --- | --- |
| Model `model` | Model sklearn dalam format skops; MLflow 3 dapat menampilkannya melalui **Logged Models / Outputs**, lalu model artifacts |
| Input example dan signature | Contoh input serta schema input/output untuk serving |
| Environment files | Dependency model seperti requirements dan Python environment |
| `evaluation/predictions.csv` | Actual, prediction, residual, dan absolute error per zone-hour |
| `evaluation/error_by_zone.csv` | Rata-rata error dan jumlah sample per zona |
| `evaluation/actual_vs_prediction.svg` | Total demand seluruh zona per jam selama validation |
| `evaluation/residual_distribution.svg` | Distribusi actual minus prediction |
| `lineage/feature_schema.json` | Feature, target, dan identitas snapshot |
| `lineage/dvc.lock`, `dvc.yaml`, `uv.lock` | Manifest data dan dependency saat file tersedia |

Untuk SVG, preview atau download lalu buka di browser. Grafik aggregate dapat menutupi error per zona; tetap baca `error_by_zone.csv`. Baseline tidak mempunyai trained model artifact karena ia langsung menggunakan `lag_24h`.

### Artifacts pada parent search

| Artifact | Isi |
| --- | --- |
| `comparison/results.csv` | Tabel baseline dan tiga kandidat, beserta hyperparameter dan metric |
| `comparison/selection_report.md` | Alasan kuantitatif memilih model, trade-off, dan batas kesimpulan |
| `comparison/selection.json` | Best run ID, model URI, parameter, snapshot, dan periode evaluasi |

Salinan laporan tersedia di `data/experiments/<PARENT_RUN_ID>/`. Folder generated ini diabaikan Git. Perubahan yang belum disimpan di Git diberi tag `git_dirty=true`; commit saja belum cukup untuk mereproduksi local edits tersebut.

## 5. Explain model selection

Aturan latihan: pilih kandidat dengan **validation MAE terendah**. Jika persis sama, gunakan RMSE lalu fit time sebagai tie breaker. Baseline adalah pembanding, bukan salah satu tiga konfigurasi model.

Contoh narasi tanpa angka yang dibuat-buat:

> We compared three configurations on the same snapshot and validation period. We selected this candidate because it had the lowest validation MAE. We also inspected RMSE, training cost, and errors by zone before considering deployment.

Jika kandidat terbaik belum mengalahkan baseline, laporkan hasil itu dan jangan menganggapnya siap produksi. Validation dipakai untuk pemilihan konfigurasi; evaluasi akhir memerlukan periode berikutnya yang belum dipakai untuk tuning. Ulangi tuning pada validation yang sama terus-menerus dapat membuat keputusan terlalu cocok pada validation itu.

## 6. Customize a single experiment

~~~powershell
uv run python scripts/train_with_mlflow.py --config-name my-candidate --learning-rate 0.08 --max-iter 150 --max-leaf-nodes 15 --l2-regularization 0.5
~~~

| Option | Fungsi |
| --- | --- |
| `--config-name` | Label konfigurasi di run name dan tag |
| `--learning-rate` | Ukuran kontribusi setiap boosting iteration |
| `--max-iter` | Maksimum boosting iterations |
| `--max-leaf-nodes` | Membatasi kompleksitas setiap tree |
| `--l2-regularization` | Penalti regularization; efeknya dievaluasi melalui validation |
| `--cpu-threads` | Batas thread untuk fit, prediction, dan model logging; default 2 |
| `--validation-days` | Banyak hari terakhir untuk validation; default 5 |
| `--snapshot` | Memilih file snapshot; ganti hanya jika memang ingin eksperimen pada data berbeda |
| `--tracking-uri` | Memilih server MLflow |
| `--experiment-name` | Memilih kelompok experiment |
| `--output-dir` | Folder salinan laporan untuk mode `--search` |

`--search` menggunakan tiga konfigurasi preset, sehingga tidak digabung dengan hyperparameter flags single run. Tanpa argumen, command lama tetap menjalankan baseline dan konfigurasi balanced.

## 7. Register after review

Salin `best_run_id` dari output search setelah memeriksa laporan dan baseline gate:

~~~powershell
uv run python scripts/register_model.py --run-id "BEST_RUN_ID"
~~~

Ganti placeholder dengan ID nyata. Command mendaftarkan model sebagai `challenger`; script registration manual tidak mengulang quality gate. Search tidak memindahkan `champion`. Promotion ke champion memerlukan keputusan review terpisah, mengikuti [Model Registry](model-registry.md).

Materi lama mungkin menyebut Staging/Production/Archived. Proyek memakai alias challenger/champion, sesuai [workflow Registry MLflow](https://mlflow.org/docs/latest/ml/model-registry/workflow/).

## Checkpoint untuk peserta

- Tunjukkan tiga kandidat dengan parameter yang benar-benar berbeda.
- Tunjukkan MAE dan RMSE pada split yang sama, plus baseline.
- Tunjukkan model artifact dan dataset inputs.
- Screenshot halaman Compare untuk tiga kandidat.
- Buka selection report dan jelaskan alasan pemilihan.
- Jelaskan kenapa FINISHED belum berarti layak dipromosikan.

## Troubleshooting: output Windows

Tracking helper mengatur stdout/stderr Windows ke UTF-8, karena MLflow menulis link run dengan karakter Unicode. Ini mencegah `UnicodeEncodeError` pada output terminal yang sebelumnya memakai cp1252. Warning MLflow mengenai integer schema adalah pengingat bahwa feature integer tidak menerima missing values; input serving tetap harus lengkap dan valid. Warning tersebut berbeda dari run FAILED.

Jika training gagal di dalam run, status FAILED tersimpan beserta metadata yang sudah tercatat. Error sebelum run dibuat, misalnya snapshot tidak ada atau CLI invalid, muncul di terminal tanpa membuat model run.
