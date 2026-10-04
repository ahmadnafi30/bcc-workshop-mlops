# Historical Replay

Salah satu pertanyaan paling penting di project ini:

> Kalau dataset kita historical dan sebenarnya sudah tersedia semua, Airflow ngambil data baru dari mana?

Jawabannya: kita pakai **historical replay**.

## The idea

Data January-March 2025 memang sudah ada, tapi production pipeline tidak akan dikasih semuanya sekaligus.

Kita bikin simulator yang me-release data sedikit demi sedikit berdasarkan tanggal.

```text
All historical data
        ↓
replay source
        ↓
simulate Jan 27
        ↓
data/raw/trips/2025-01-27.parquet
```

Run berikutnya:

```text
simulate Jan 28
        ↓
data/raw/trips/2025-01-28.parquet
```

Dari sisi Airflow, behavior-nya jadi seperti data production yang benar-benar baru datang.

## Why not just train on everything?

Kalau dari awal kita kasih Jan + Feb + Mar ke model, kita kehilangan banyak konsep MLOps yang mau ditunjukkan:

- incremental ingestion,
- new data arrival,
- production prediction,
- delayed evaluation,
- performance monitoring,
- retraining trigger,
- dataset version changes.

Historical replay bikin semua itu bisa didemokan tanpa harus nunggu tiga bulan beneran.

## Replay timeline

Initial setup:

```text
Jan 01 - Jan 21
initial training data

Jan 22 - Jan 26
validation data
```

Setelah model awal siap:

```text
Jan 27 -> production day #1
Jan 28 -> production day #2
Jan 29 -> production day #3
...
Mar 31 -> production day N
```

Satu hari production tidak berarti workshop harus nunggu 24 jam. Saat demo, satu DAG run bisa merepresentasikan satu hari.

## Planned scripts

### `bootstrap_data.py`

Tugasnya:

```text
download TLC monthly data
        ↓
load taxi zone lookup
        ↓
prepare workshop dataset
        ↓
build replay source
```

Script ini cukup dijalankan saat setup.

### `simulate_daily_data.py`

Tugasnya me-release satu tanggal tertentu.

```bash
python scripts/simulate_daily_data.py --date 2025-01-27
```

hasilnya:

```text
data/raw/trips/2025-01-27.parquet
```

Lalu Airflow memproses batch yang baru muncul.

## Airflow's role

Airflow tidak menciptakan data dan Airflow juga tidak harus mengambil data dari API.

Yang Airflow lakukan adalah **orchestrate workflow ketika batch data tersedia**.

Contoh flow:

```text
release / detect daily batch
          ↓
validate raw data
          ↓
aggregate hourly demand
          ↓
feature engineering
          ↓
save processed batch
```

## Logical date

Replay date nanti bisa kita kaitkan dengan Airflow logical date.

```text
Airflow logical date
2025-02-05

        ↓

process data for
2025-02-05
```

Dengan begitu DAG lebih reproducible. Kalau logical date yang sama dirun ulang, pipeline tahu batch mana yang harus diproses.

Ini juga jadi pintu masuk buat bahas **idempotency**.

## Prediction and ground truth

Dalam real production, saat kita memprediksi demand jam berikutnya, actual demand belum diketahui.

```text
17:00
predict demand for 18:00

18:00-18:59
actual trips happen

after 19:00
actual 18:00 demand is available
```

Historical replay memungkinkan behavior ini disimulasikan walaupun data aslinya sebenarnya sudah ada.

Simulator cuma perlu memastikan pipeline tidak mengintip future data sebelum waktunya.

## Retraining flow

```text
new batch arrives
      ↓
process data
      ↓
evaluate recent predictions
      ↓
calculate recent MAE
      ↓
performance still okay?
   /             \
 yes             no
  ↓               ↓
 end          retrain model
                   ↓
                MLflow
                   ↓
          compare candidate
            vs current model
```

Jadi Airflow punya peran yang natural, bukan sekadar menjalankan `train.py` pakai schedule tanpa alasan.

## Is this fake production?

Kita memang mensimulasikan waktu, tapi konsep pipeline-nya tetap real.

Historical replay useful untuk backtesting, pipeline testing, reproducing incidents, validating retraining logic, dan testing time-dependent features.

Yang kita fake cuma **speed of time**. Data flow dan dependency-nya tetap dibuat seperti production system.