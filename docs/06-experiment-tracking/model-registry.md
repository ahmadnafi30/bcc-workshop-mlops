# MLflow Model Registry

Experiment Tracking dan Model Registry punya kerjaan yang beda.

Tracking dipakai buat nyatet semua percobaan. Registry dipakai buat ngatur model yang memang sudah dianggap candidate untuk dipakai sistem lain.

Flow workshop kita:

```text
MLflow experiment run
        ↓
model artifact
        ↓
register
        ↓
challenger
        ↓
review
        ↓
champion
```

## 1. Cari model run

Setelah:

```bash
uv run python scripts/train_with_mlflow.py
```

terminal bakal print run id untuk gradient boosting.

Contohnya:

```text
model -> MAE 10.123, run 8d4...
```

Run id itu yang kita register.

## 2. Register sebagai challenger

```bash
uv run python scripts/register_model.py --run-id <RUN_ID>
```

Hasil pertama kira-kira:

```text
taxi-demand-forecasting-model
└── version 1
    └── alias: challenger
```

Kalau nanti ada model baru:

```text
taxi-demand-forecasting-model
├── version 1
└── version 2
    └── alias: challenger
```

Alias `challenger` pindah ke candidate terbaru tanpa consumer harus tahu version number.

## 3. Review dulu

Kita sengaja nggak langsung bikin model baru jadi production.

Sebelum promote, kita bisa cek:

```text
MAE
RMSE
experiment params
training snapshot
model artifact
```

Nanti setelah monitoring dan retraining masuk, review ini bisa punya rule yang lebih otomatis.

Untuk sekarang kita bikin explicit supaya konsepnya kelihatan.

## 4. Promote ke champion

Misalnya version 1 sudah oke:

```bash
uv run python scripts/promote_model.py --version 1
```

Registry jadi:

```text
taxi-demand-forecasting-model
└── version 1
    ├── challenger
    └── champion
```

Kalau besok version 2 lebih bagus, kita tinggal:

```bash
uv run python scripts/promote_model.py --version 2
```

Sekarang alias `champion` pindah ke version 2.

## Kenapa pakai alias?

Tanpa alias, API bisa saja load:

```text
models:/taxi-demand-forecasting-model/1
```

Masalahnya setiap model update, code API juga harus diganti ke version 2, 3, 4, dan seterusnya.

Dengan alias:

```text
models:/taxi-demand-forecasting-model@champion
```

FastAPI nanti cukup load URI itu terus.

Model version di belakangnya boleh berubah tanpa hard-code version baru di application code.

## Champion dan challenger

Di workshop ini artinya sederhana:

**challenger**

candidate baru yang lagi kita evaluate.

**champion**

model yang sekarang dipilih untuk dipakai production.

Ini bukan fitur wajib MLflow. Nama alias sebenarnya bebas. Kita pilih dua nama ini karena gampang dipakai buat ngejelasin lifecycle model.

## Next

Setelah registry ini siap, kita sudah punya boundary yang enak buat model serving:

```text
FastAPI
   ↓
load
models:/taxi-demand-forecasting-model@champion
   ↓
predict
```

Jadi FastAPI nanti nggak perlu tahu model ditrain pakai file apa atau version berapa. Dia cuma perlu tahu siapa current champion.
