# CI/CD Concepts

Sekarang project kita sudah punya code, tests, Docker image, dan beberapa service.

Problem berikutnya:

> setiap ada perubahan code, siapa yang ngecek semuanya masih aman?

Kalau jawabannya masih:

```text
jalanin pytest sendiri
coba docker build sendiri
```

berarti prosesnya masih bergantung ke manusia.

Di sini CI/CD mulai kepake.

## CI

CI atau **Continuous Integration** fokus ke pertanyaan:

> perubahan code ini aman buat digabung?

Flow project kita:

```text
push / pull request
        ↓
install project
        ↓
run tests
        ↓
validate Docker Compose
        ↓
build Docker images
        ↓
pass / fail
```

Jadi CI bukan deployment. CI adalah quality gate sebelum perubahan dianggap sehat.

## CD

CD bisa berarti Continuous Delivery atau Continuous Deployment.

Di workshop ini kita pakai **Continuous Delivery**.

```text
CI success
    ↓
build service images
    ↓
tag images
    ↓
push to GHCR
```

Setelah itu image sudah siap dipakai deployment environment, tapi kita belum otomatis deploy ke cloud/server karena project ini memang belum punya target infrastructure.

Itu beda dengan Continuous Deployment:

```text
CI success
    ↓
build image
    ↓
push registry
    ↓
automatic deploy
    ↓
production
```

Kita belum sampai bagian terakhir itu.

## Kenapa dipisah?

Biar jelas boundary-nya:

```text
CI
apakah perubahan ini aman?

CD
kalau aman, artifact-nya dikirim ke mana?
```

Artifact yang kita deliver sekarang adalah Docker image.

## Pipeline project

```text
developer
   ↓
git push
   ↓
GitHub
   ↓
CI workflow
   ├── pytest
   └── Docker build
          ↓
       success
          ↓
Container Delivery workflow
          ↓
        GHCR
          ↓
api / mlflow / airflow images
```

Jadi setelah tahap ini, source code bukan satu-satunya output project. Kita juga punya container image yang bisa dipakai environment lain.