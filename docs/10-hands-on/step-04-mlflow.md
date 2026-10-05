# Step 4 — MLflow: Dari “Kayaknya Run Kemarin Bagus” Jadi Experiment yang Bisa Ditelusuri

Sekarang kita punya reproducible snapshot.

Tapi experiment history masih manual.

Kita butuh system yang record:

~~~text
input context
parameter
metric
artifact
~~~

MLflow masuk di sini.

---

## Goal

Setelah step ini:

- local MLflow server jalan,
- baseline dan main model logged,
- kalian bisa inspect run,
- model masuk Registry,
- challenger dipromote ke champion secara explicit.

---

## 1. Start shared MLflow server

~~~bash
uv run python scripts/start_mlflow.py
~~~

Open:

~~~text
http://127.0.0.1:5000
~~~

Keep terminal running.

Kalau service MLflow sudah berjalan melalui Docker di port 5000, gunakan server
tersebut dan langsung lanjut ke training. Set
`MLFLOW_TRACKING_URI=http://127.0.0.1:5000` pada terminal script manual.

### Kenapa bukan raw mlflow server command?

Helper project ensure state tersimpan di:

~~~text
.mlflow/
~~~

Folder yang sama nanti dipakai Docker mode.

Jadi experiment continuity terjaga.

---

## 2. Run tracked training

Terminal lain:

~~~bash
uv run python scripts/train_with_mlflow.py
~~~

Model HGB disimpan menggunakan format `skops`. Daftar trusted types di
`src/tracking/mlflow_tracking.py` berisi tipe internal yang diperlukan model
workshop, supaya artifact bisa dimuat kembali. Dependency MLflow minimal 3.16.1
menyediakan konfigurasi ini.

Observe output.

Biasanya ada run ID.

Jangan cuma copy.

Understand:

~~~text
one execution
→ one MLflow run
~~~

---

## 3. Buka MLflow UI

Cari experiment taxi demand.

Lihat run baseline dan HGB.

Klik main model run.

Cari:

- Parameters,
- Metrics,
- Tags,
- Artifacts.

---

## 4. Interactive question

Cari dataset_sha256.

Pertanyaan:

> “Kalau dua run pakai filename snapshot sama tapi SHA beda, apa artinya?”

Content berbeda.

Filename alone bukan identity kuat.

---

## 5. Compare baseline vs model

Gunakan compare UI.

Jangan cuma lihat ranking.

Coba cari:

~~~text
model_type
MAE
RMSE
dataset snapshot
stage
~~~

MLflow UI harus membantu explain experiment, bukan cuma jadi tabel warna-warni.

---

## 6. Register model

Ambil model run ID.

~~~bash
uv run python scripts/register_model.py --run-id <RUN_ID>
~~~

Open Model Registry.

Sekarang main model bukan cuma artifact experiment.

Dia punya registered version.

---

## 7. Lihat challenger alias

Candidate baru diberi challenger.

Pertanyaan:

> “Kenapa belum champion?”

Karena registration bukan approval.

---

## 8. Promote

Setelah review:

~~~bash
uv run python scripts/promote_model.py --version <VERSION>
~~~

Sekarang champion alias point ke selected version.

---

## 9. Trace lineage

Coba dari champion UI trace balik:

~~~text
champion
↓
version
↓
source run
↓
metric
parameter
dataset hash
~~~

Kalau chain ini jelas, Registry + Tracking sudah connect.

---

## Mini challenge

Kalau besok version 2 promoted, apakah FastAPI source harus di-edit dari version 1 ke version 2?

Tidak.

API load champion alias.

---

## Checkpoint

Coba explain:

- experiment,
- run,
- parameter,
- metric,
- artifact,
- registered model,
- version,
- challenger,
- champion.

Kalau sudah, kita masuk orchestration.
