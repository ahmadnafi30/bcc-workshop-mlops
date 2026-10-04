# Model Serving

Setelah model selesai ditrain dan masuk MLflow Registry, next problem-nya bukan training lagi.

Sekarang kita perlu jawab:

> application lain pakai model ini gimana?

Di project ini boundary-nya kita bikin lewat FastAPI.

```text
client
  ↓
FastAPI
  ↓
online feature construction
  ↓
MLflow champion model
  ↓
prediction
```

## Request-nya sengaja simple

Client nggak perlu tahu feature engineering internal model.

Request cukup:

```json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
```

Kita **nggak** minta client ngirim:

```text
lag_1h
lag_24h
lag_168h
rolling_mean_3h
rolling_mean_24h
```

Karena feature seperti itu adalah tanggung jawab serving pipeline, bukan caller.

## Online feature construction

API ambil processed demand dari:

```text
data/processed/demand/
```

Untuk target:

```text
2025-01-28 18:00
```

feature provider cuma boleh baca sampai:

```text
2025-01-28 17:00
```

Lalu dibangun:

```text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
```

Jadi serving path punya leakage rule yang sama dengan training.

Kalau history 168 jam belum lengkap, API fail dengan response 422 daripada bikin prediction dari feature yang salah.

## Target datetime

Untuk sekarang timestamp dianggap sebagai **waktu lokal NYC** dan request harus pas di awal jam.

Valid:

```text
2025-01-28T18:00:00
```

Tidak valid:

```text
2025-01-28T18:30:00
```

Timezone-aware datetime juga belum kita pakai di API workshop supaya konsisten dengan TLC timestamp yang kita proses sebagai local wall-clock time.

## Model loading

API tidak load hard-coded model version seperti:

```text
models:/taxi-demand-forecasting-model/1
```

Yang dipakai:

```text
models:/taxi-demand-forecasting-model@champion
```

Loader cek version yang sekarang ditunjuk alias `champion`.

Kalau alias pindah:

```text
version 1
   ↓
version 2
```

request berikutnya akan reload model version baru.

Jadi application code nggak perlu diedit cuma karena ada model baru.

## Prediction output

Response kira-kira:

```json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00",
  "predicted_trip_count": 147.8,
  "model_name": "taxi-demand-forecasting-model",
  "model_version": "2",
  "model_alias": "champion",
  "run_id": "abc123",
  "model_uri": "models:/taxi-demand-forecasting-model@champion"
}
```

Model prediction tetap float karena regression output tidak harus integer.

Untuk sekarang hasil negatif dibatasi minimum nol karena jumlah pickup secara domain nggak mungkin negatif.
