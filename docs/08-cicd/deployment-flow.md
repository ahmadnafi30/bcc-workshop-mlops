# Container Delivery Flow

Setelah CI sukses di `main`, workflow CD build ulang image dari commit yang sama lalu push ke GitHub Container Registry atau GHCR.

## Image names

Project publish tiga image:

```text
ghcr.io/<owner>/bcc-workshop-mlops-api
ghcr.io/<owner>/bcc-workshop-mlops-mlflow
ghcr.io/<owner>/bcc-workshop-mlops-airflow
```

Owner otomatis diambil dari GitHub context, jadi workflow nggak hard-code username.

## Tags

Setiap image punya SHA tag:

```text
sha-a1b2c3d
```

dan image dari main juga punya:

```text
latest
```

`latest` adalah pointer yang bisa pindah. SHA tag ngasih tahu exact code revision yang menghasilkan image itu, jadi lebih enak buat rollback dan audit.

## Flow lengkap

```text
commit A
   ↓
CI
   ↓
tests pass
Docker builds pass
   ↓
CD
   ↓
GHCR

api
├── latest
└── sha-...

mlflow
├── latest
└── sha-...

airflow
├── latest
└── sha-...
```

## Kenapa build lagi di CD?

CI build memastikan image bisa dibangun. CD build menghasilkan artifact yang benar-benar dipublish.

CD checkout exact commit SHA yang sebelumnya lolos CI, jadi kita nggak sengaja publish revision lain yang belum dites.

## Continuous delivery, bukan deployment

Sampai tahap ini pipeline selesai di:

```text
GHCR
```

Belum ada SSH ke server, `kubectl apply`, cloud deploy, atau production restart.

Kalau nanti project punya VPS, Kubernetes, ECS, Cloud Run, atau target lain, baru kita tambahin deployment job setelah delivery.

## Lihat package

Setelah workflow pertama berhasil, image akan muncul di bagian **Packages** akun/repository GitHub.

Kalau repository atau package private, consumer perlu authentication untuk pull image.

## Pull image

Contoh secara umum:

```bash
docker pull ghcr.io/<owner>/bcc-workshop-mlops-api:latest
```

Untuk exact revision:

```bash
docker pull ghcr.io/<owner>/bcc-workshop-mlops-api:sha-<commit>
```

## Workshop takeaway

Yang penting bukan hafal YAML-nya. Yang perlu kebawa adalah dependency:

```text
code change
   ↓
verify
   ↓
package
   ↓
deliver
```

GitHub Actions cuma tool yang mengotomatisasi lifecycle itu.