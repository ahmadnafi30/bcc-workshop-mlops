# GitHub Actions

GitHub Actions jadi automation engine buat CI/CD project ini.

Workflow disimpan di:

```text
.github/workflows/
├── ci.yml
└── cd.yml
```

## CI workflow

`ci.yml` jalan saat:

```text
push ke main
pull request ke main
manual trigger
```

Ada dua job utama.

### Python tests

```text
checkout
   ↓
setup uv
   ↓
install Python
   ↓
uv sync
   ↓
pytest
```

Command test yang dijalankan runner:

```bash
uv run pytest -q
```

Jadi CI menggunakan workflow yang sama dengan cara kita jalanin project lokal.

### Docker build

Job kedua pakai matrix:

```text
api
mlflow
airflow
```

GitHub build ketiga target Dockerfile. Di CI `push` diset false, jadi image cuma dibuild buat validasi dan belum dikirim ke registry.

Sebelum build, workflow juga menjalankan:

```bash
docker compose config --quiet
```

supaya error syntax atau interpolation di Compose ketahuan lebih awal.

## Cache

Docker build menggunakan GitHub Actions cache yang dipisah per target. uv setup juga pakai cache supaya install berikutnya lebih cepat.

## Concurrency

CI punya `cancel-in-progress: true`.

Kalau commit baru masuk ke branch yang sama saat CI lama masih jalan, run lama bisa dihentikan dan runner fokus ke revision terbaru.

## CD workflow

`cd.yml` menunggu workflow `CI` selesai.

Container image baru dipublish kalau:

```text
CI conclusion = success
event = push
branch = main
```

Jadi pull request nggak bisa publish image hanya karena membuka PR.

Manual trigger tetap tersedia buat demo.

## Permissions

CI cuma butuh:

```text
contents: read
```

Sedangkan delivery butuh:

```text
contents: read
packages: write
```

`packages: write` dipakai buat push image ke GitHub Container Registry.

Kita pakai built-in `GITHUB_TOKEN`, jadi workshop nggak perlu bikin Docker registry password sendiri.