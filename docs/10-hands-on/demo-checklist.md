# Presenter Demo Checklist — Biar Workshop Live Nggak Bergantung Sama Keberuntungan

Presenters:

- **Ahmad Nafi Mubarok**
- **Fatoni Murfid Syafii**

Gunakan [Modul Workshop](../workshop-module.md) untuk agenda dan checkpoint kelas,
serta [Quickstart Grafana](dashboard-quickstart.md) untuk preflight demo lengkap.

Live demo itu beda dengan local development.

Yang bisa fail bukan cuma code.

Ada:

- venue Wi-Fi,
- package download,
- port conflict,
- Docker cache,
- browser login,
- laptop battery. 😭

Jadi kita prepare.

---

## H-1: repository

Check:

~~~bash
git status
git branch
uv run pytest
uv run ruff check src api scripts tests
uv run --group docs mkdocs build --strict
~~~

Pastikan main stable.

---

## H-1: data

Jangan bergantung ke live TLC download kalau venue internet uncertain.

Pre-bootstrap data.

Verify required dates.

---

## H-1: MLflow

Prepare known-good backup:

- experiment,
- model run,
- registered version,
- champion.

Live demo tetap bisa train, tapi backup prevents session stuck.

---

## H-1: Docker images

Pre-build:

~~~bash
docker compose build
~~~

First Airflow build bisa lama.

Workshop bukan tempat ideal nonton pip install 10 menit. 😭

---

## Before audience arrives

Check ports:

~~~text
3000
5000
8000
8080
9090
~~~

Close unrelated services.

---

## Browser tabs

Siapkan:

1. Docs
2. GitHub Actions
3. MLflow
4. Airflow
5. Swagger
6. Prometheus Targets
7. Grafana

Urutkan tab sesuai teaching flow.

---

## Teaching flow recommendation

### Opening

Jangan langsung sebut 10 tools.

Mulai:

> “Model sudah jadi. Terus sekarang problem berikutnya apa?”

Build curiosity.

### Data

Show one trip row.

Then show hourly aggregate.

Biar transformation concrete.

### Feature

Ask audience:

> “Kalau target 18:00, actual 18:00 boleh jadi feature nggak?”

Make leakage interactive.

### Baseline

Before showing model metric, ask:

> “Kalau kemarin jam yang sama dipakai prediction, kira-kira strong nggak?”

### DVC

Ask:

> “Kalau feature file berubah tapi nama sama, model lama pakai yang mana?”

### MLflow

Show messy experiment scenario first.

Then UI.

### Airflow

Draw DAG manually before UI.

Audience harus predict graph dulu.

### FastAPI

Ask:

> “Client perlu kirim lag_168h nggak?”

Then show simple request.

### Docker

Ask why localhost from container fails.

### CI/CD

Show real PR run.

### Monitoring

Siapkan processed demand Jan 28 lewat daily replay DAG sebelum generate traffic.

Tunjukkan tiga momen:

1. Sebelum traffic: status evaluasi dan waktu summary terakhir.
2. Sesudah traffic: prediction rate, latency, versi serving, dan response 4xx.
3. Sesudah evaluasi: MAE, threshold, sample count, dan status model.

Gunakan `--min-samples 100000` sekali untuk menunjukkan status sample belum
cukup, kemudian evaluasi ulang dengan default. Cocokkan **Serving Model** dengan
**Evaluated Model** dan jelaskan dua clock: waktu job nyata dan target replay NYC.

### Retraining

Show healthy path too.

Emphasize:

> no retrain can be correct.

---

## Backup strategy

Kalau live training fail:

- use prepared MLflow run,
- continue Registry section.

Kalau Docker fail:

- use local services,
- explain intended container boundary.

Kalau Grafana fail:

- show Prometheus raw metrics and provisioned dashboard config.

Goal workshop = understanding lifecycle.

Bukan proving laptop perfect.

---

## Final audience challenge

Minta satu volunteer explain:

~~~text
data
→ model
→ serving
→ monitoring
→ retraining
~~~

Then presenters bantu fill gaps.

Kalau audience bisa explain causal flow, session berhasil.
