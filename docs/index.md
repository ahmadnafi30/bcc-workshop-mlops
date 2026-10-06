# BCC Workshop — MLOps 👋

Satu perjalanan belajar untuk memahami bagaimana model Machine Learning disiapkan, dilacak, dijalankan sebagai API, lalu dipantau. Kita belajar dari use case nyata—NYC Yellow Taxi demand forecasting—dan membahas tools setelah problem-nya jelas.

Dibawakan oleh **Ahmad Nafi Mubarok** dan **Fatoni Murfid Syafii**.

[Mulai dari sini](00-start-here.md){ .md-button .md-button--primary }
[Lihat workshop lengkap](workshop-module.md){ .md-button }
[Coba quickstart dashboard](10-hands-on/dashboard-quickstart.md){ .md-button }

## Pilih jalurmu

=== "Saya baru belajar MLOps"

    Mulai dengan [Mulai di Sini](00-start-here.md). Halaman ini menjelaskan use case, fungsi tiap tool, dan apa yang perlu dilihat di Airflow, MLflow, FastAPI, Prometheus, serta Grafana.

=== "Saya ingin mencoba demo"

    Ikuti [Quickstart Grafana](10-hands-on/dashboard-quickstart.md) untuk membuat alur lengkap dari data taxi sampai hasil evaluasi terlihat di dashboard.

=== "Saya ikut sesi workshop"

    Buka [Modul Workshop](workshop-module.md) untuk agenda kelas, checkpoint, tugas, dan panduan fasilitator. Untuk praktik peserta, ikuti [Step 0 sampai Step 10](10-hands-on/setup.md) secara berurutan.

## Apa yang akan kita bangun?

Kita memprediksi jumlah pickup taxi untuk setiap zona Manhattan pada satu jam berikutnya. Di sepanjang workshop, alurnya berkembang seperti ini:

~~~text
Taxi data → features → training snapshot → model training
     → MLflow tracking → model registry → prediction API
     → Prometheus + Grafana → evaluasi → retraining bila diperlukan
~~~

| Bagian | Pertanyaan utama | Materi |
| --- | --- | --- |
| Data | Data apa yang boleh dipakai model? | [Use case](02-use-case/problem-statement.md) |
| Training | Bagaimana membandingkan model dengan baseline? | [Baseline](06-experiment-tracking/baseline-training.md) |
| Tracking | Run mana yang menghasilkan model ini? | [MLflow](06-experiment-tracking/experiment-tracking.md) |
| Orchestration | Bagaimana pekerjaan dijalankan dalam urutan yang benar? | [Airflow](03-tools/airflow.md) |
| Serving | Bagaimana aplikasi meminta prediction? | [FastAPI](07-model-serving/fastapi.md) |
| Monitoring | Apakah service sehat dan model masih akurat? | [Grafana](09-monitoring/grafana.md) |

## Service lokal

Setelah stack workshop dijalankan, service umumnya tersedia di alamat berikut. Port bisa berbeda jika diubah di konfigurasi lokal.

| Service | Alamat | Untuk apa? |
| --- | --- | --- |
| MLflow | [localhost:5000](http://localhost:5000) | Melihat experiments dan model registry |
| Airflow | host port dari `docker compose ps airflow` | Melihat dan menjalankan DAG |
| FastAPI | [localhost:8000/docs](http://localhost:8000/docs) | Mencoba endpoint API |
| Prometheus | [localhost:9090](http://localhost:9090) | Memeriksa metrics dan targets |
| Grafana | [localhost:3000](http://localhost:3000) | Membaca dashboard |

Port pada kolom `PORTS` memakai format `HOST:CONTAINER`. Jika tertulis `127.0.0.1:18081->8080/tcp`, buka `http://localhost:18081`. Gunakan host port yang tampil di laptopmu.

!!! info "UI terbuka tapi masih kosong?"
    Service yang hidup belum otomatis punya data. MLflow perlu training run, Airflow perlu DAG yang di-trigger, dan panel Grafana perlu prediction traffic atau hasil evaluasi. Mulai dari [panduan pemula](00-start-here.md#sebelum-membuka-dashboard), lalu gunakan [troubleshooting](10-hands-on/troubleshooting.md) bila ada langkah yang gagal.

## Butuh referensi cepat?

- Cari istilah di [Glossary](glossary.md).
- Lihat error berdasarkan gejalanya di [Troubleshooting](10-hands-on/troubleshooting.md).
- Buka halaman [Hands-on Workshop](10-hands-on/setup.md) untuk melanjutkan step berikutnya.
