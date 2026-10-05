# Presenter Checklist — Ahmad Nafi & Fatoni

Halaman ini khusus supaya workshop day lebih smooth.

Presenter:

- **Ahmad Nafi Mubarok**
- **Fatoni Murfid Syafii**

Tujuan checklist bukan bikin demo scripted kaku.

Tujuannya mengurangi failure yang sebenarnya bisa dicegah.

---

# H-1 / sebelum sesi

## Repository

Check:

~~~text
main latest?
develop aligned?
CI green?
no accidental generated data committed?
~~~

## Dependencies

~~~bash
uv sync
uv sync --group airflow
uv sync --group docs
~~~

## Tests

~~~bash
uv run pytest
uv run ruff check src api scripts tests
uv run --group docs mkdocs build --strict
~~~

---

# Data preparation

Internet venue bisa random.

Recommended pre-download TLC data.

Pastikan:

~~~text
zone lookup ready
monthly source ready
replay source ready
~~~

Tapi saat demo tetap tunjukkan command bootstrap dan explain what it would do.

---

# MLflow backup

Punya known-good:

- experiment,
- model run,
- registered model,
- champion alias.

Kenapa?

Kalau live training unexpected slow, workshop tetap bisa lanjut ke Registry/API.

Prepared backup bukan cheating.

Itu demo reliability.

---

# Docker pre-build

Kalau waktu sesi limited:

~~~bash
docker compose build
~~~

sebelum kelas.

Participants tetap belajar command up/build, tapi presenter tidak buang 15 menit nunggu dependency download.

---

# Ports check

Pastikan tidak ada random service di:

~~~text
3000
5000
8000
8080
9090
~~~

---

# Browser tabs yang enak sudah ready

1. Docs
2. GitHub repo
3. GitHub Actions
4. MLflow
5. Airflow
6. FastAPI Swagger
7. Prometheus Targets
8. Grafana

Jangan baru cari URL saat presentasi.

---

# Teaching flow recommendation

## Opening

Mulai dari model-only pain.

Jangan langsung:

> “Hari ini kita belajar DVC.”

Mulai:

> “Kalau model kalian bagus, gimana orang lain reproduce?”

---

## Data

Show:

~~~text
trip
→ hourly demand
→ features
~~~

Jangan skip leakage explanation.

---

## DVC

Tanya peserta dulu:

> “Kalau features.parquet berubah besok, model lama pakai version mana?”

Baru show DVC.

---

## MLflow

Tanya:

> “Kalau 20 experiment, kalian track pakai apa?”

Baru show UI.

---

## Airflow

Draw manual steps first.

Then show DAG graph.

Biar visual Airflow jadi answer, bukan mystery.

---

## FastAPI

Swagger interactive.

Ask one participant choose zone ID.

Show response + model version.

---

## Docker

Highlight internal network.

Ini tempat banyak peserta usually “ohhh”.

---

## CI/CD

Open real Actions run.

Jangan cuma screenshot.

Show green job + one log.

---

## Monitoring

Generate real HTTP traffic.

Watch Grafana move.

Then explain model MAE delayed.

---

## Retraining

Show healthy case first.

Important:

> “Tidak retrain juga bisa menjadi correct result.”

Kalau perlu demo degraded path, presenter bisa adjust threshold on a controlled branch/run, tapi explain bahwa itu demo setting.

---

# Kalau demo fail live

Rule:

~~~text
Do not spend 20 minutes silently debugging.
~~~

1. Identify layer.
2. Explain what should happen.
3. Show log.
4. Switch to prepared state if needed.
5. Continue learning objective.

Workshop tujuan utamanya understanding, bukan stress test Wi-Fi.

---

# Closing questions

Tanya peers:

### Q1

Kalau API latency bagus tapi model MAE jelek, problem ada di mana?

### Q2

Bedanya DVC dan MLflow?

### Q3

Kenapa Airflow dan GitHub Actions dua-duanya automation tapi nggak redundant?

### Q4

Kenapa challenger nggak langsung champion?

Kalau mereka bisa jawab, workshop story berhasil.
