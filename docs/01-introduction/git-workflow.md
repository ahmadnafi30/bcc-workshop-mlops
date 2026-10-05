# Git Workflow — Kenapa Nggak Langsung Commit ke Main?

## Personal project vs collaborative project

Kalau project masih eksperimen pribadi, direct commit ke main kadang masih okay.

Tapi repo ini dipakai untuk:

- workshop,
- collaboration,
- future improvement,
- stable demo.

Kita butuh sedikit boundary supaya work-in-progress nggak langsung masuk stable version.

Flow kita:

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

---

# main — stable workshop release

Anggap main sebagai:

> “Version yang cukup aman buat dipakai presenter dan participant.”

Main seharusnya:

- CI green,
- docs build,
- Docker build,
- sudah lewat integration branch.

Kita nggak develop feature langsung di main.

---

# develop — integration area

Develop adalah tempat completed feature bertemu.

Bayangin ada dua branch:

~~~text
feat/new-dashboard
feat/new-api
~~~

Individually mungkin dua-duanya works.

Tapi begitu digabung, bisa conflict behavior.

Develop memberi kita ruang:

~~~text
feature A
       → develop → integration checks
   /
feature B
~~~

baru setelah stable release ke main.

---

# feat/* — workbench

Feature branch tempat kita bebas iterate.

Contoh:

~~~text
feat/add-data-drift
feat/add-model-comparison
~~~

Di sini boleh punya beberapa commits sementara.

Nanti saat PR merge, squash bisa bikin history integration tetap clean.

---

# fix/*

Bug fix.

~~~text
fix/rolling-window-leakage
~~~

---

# docs/*

Documentation-only change.

~~~text
docs/rewrite-airflow-guide
~~~

Branch yang sedang kalian baca sekarang juga logically cocok ke category ini.

---

# chore/*

Maintenance.

Contoh:

~~~text
chore/update-lint-config
~~~

---

# Typical workflow

Start dari develop:

~~~bash
git switch develop
git pull
~~~

Create feature:

~~~bash
git switch -c feat/my-feature
~~~

Work.

Commit:

~~~bash
git add .
git commit -m "feat: add my feature"
~~~

Push:

~~~bash
git push -u origin feat/my-feature
~~~

PR:

~~~text
feat/my-feature
→
develop
~~~

Setelah develop stable:

~~~text
develop
→
main
~~~

---

# Kenapa nggak feat → main?

Karena main bukan integration sandbox.

Kita ingin stable release punya satu predictable promotion path.

Ini juga membantu presenter:

> “Kalau main green, itu workshop release.”

---

# Branch policy di CI

Workflow check PR direction.

Allowed:

~~~text
feat/* → develop
fix/* → develop
docs/* → develop
chore/* → develop

develop → main
~~~

Kalau feature langsung ke main, check fail.

---

# Branch protection vs CI policy

CI branch policy membantu enforce convention.

Tapi GitHub Ruleset / Branch Protection lebih strict karena bisa benar-benar prevent direct push.

Workshop repo bisa menambah ruleset di repository settings.

Konsepnya beda:

~~~text
CI policy
→ check

branch protection
→ enforce repository permission/rule
~~~

---

# Commit message style

Kita pakai simple Conventional Commit style.

| Prefix | Meaning |
| --- | --- |
| feat | fitur |
| fix | bug fix |
| docs | dokumentasi |
| refactor | restructure tanpa behavior baru |
| test | test |
| ci | CI/CD |
| chore | maintenance |

Good:

~~~text
feat: add prediction monitoring
fix: prevent rolling leakage
docs: explain Airflow XCom
~~~

Less helpful:

~~~text
update
fix again
change stuff
~~~

---

# Kenapa history matters?

Enam bulan kemudian kita ingin lihat:

~~~text
feat: add Airflow orchestration
feat: add FastAPI serving
feat: add monitoring lifecycle
~~~

Itu readable.

Dibanding:

~~~text
fix
fix2
final
final bener
hehe
~~~

History adalah documentation juga.

---

# Squash merge

Feature branch mungkin punya:

~~~text
WIP docs
fix typo
rewrite
fix formatting
~~~

Saat merge ke develop, squash bisa turn menjadi:

~~~text
docs: rewrite workshop material for beginners
~~~

Cleaner.

---

# Release merge

develop → main biasanya kita preserve sebagai release event.

Jadi history main bisa menunjukkan:

~~~text
feature milestones
↓
release commit
~~~

---

# Mini challenge

Coba jawab:

> Kalian sedang menambah satu Grafana panel baru. Branch start dari mana dan PR ke mana?

Answer:

~~~text
start from develop
↓
feat/add-grafana-panel
↓
PR to develop
~~~

Kalau develop stable:

~~~text
develop
↓
PR to main
~~~

---

# Takeaway

Branching strategy bukan karena “professional repo harus banyak branch”.

Kita pakai branch karena ada lifecycle:

~~~text
work
→ integrate
→ release
~~~

Tooling kita hanya membuat lifecycle itu lebih explicit.
