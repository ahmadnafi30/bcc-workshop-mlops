# Git Workflow — Kenapa Kita Nggak Langsung Commit ke Main?

Kalau project personal kecil, commit langsung ke main itu convenient.

Tapi begitu repository mulai dipakai team, workshop, atau ada release yang harus stabil, kita butuh sedikit structure.

Project ini pakai:

~~~text
feat/* / fix/* / docs/* / chore/*
              ↓
           develop
              ↓
            main
~~~

Ini bukan satu-satunya branching strategy di dunia.

Tapi cukup simple buat workshop dan cukup realistis buat ngenalin integration flow.

---

## main = stable release

Main seharusnya merepresentasikan version yang:

- sudah lewat integration,
- CI green,
- siap didemokan,
- nggak berisi half-finished feature.

Mental model:

> Kalau presenter clone main pagi workshop, harusnya aman.

---

## develop = integration branch

Develop adalah tempat feature selesai ketemu satu sama lain.

Bayangin dua feature:

~~~text
feat/new-api
feat/new-monitoring
~~~

Masing-masing green sendiri.

Tapi pas digabung, bisa conflict atau behavior berubah.

Develop kasih stage buat integration sebelum stable release.

---

## feat/* = workbench

Feature branch itu tempat eksperimen implementation.

Contoh:

~~~text
feat/add-weather-data
feat/improve-api-cache
~~~

Di sini commit bisa beberapa kali.

Setelah feature coherent, buka PR ke develop.

---

## fix/*

Untuk bug fix.

Contoh:

~~~text
fix/prevent-feature-leakage
~~~

Kenapa naming useful?

Karena dari branch name aja reviewer langsung tahu intent.

---

## docs/*

Documentation-only work.

Contoh branch yang kita pakai buat rewrite ini:

~~~text
docs/interactive-indonesia-workshop
~~~

Walaupun “cuma docs”, CI tetap jalan.

Karena docs adalah workshop product.

---

## Flow feature normal

~~~bash
git switch develop
git pull
git switch -c feat/my-feature
~~~

Work.

Commit.

~~~bash
git add .
git commit -m "feat: add my feature"
git push -u origin feat/my-feature
~~~

Open PR:

~~~text
feat/my-feature
↓
develop
~~~

Setelah develop stable:

~~~text
develop
↓
main
~~~

---

## Kenapa PR?

Pull Request bukan cuma merge button.

PR jadi review surface.

Kita bisa lihat:

- diff,
- CI status,
- comment,
- discussion,
- approval.

Bahkan kalau team cuma dua orang, PR history useful buat audit kenapa change masuk.

---

## Commit message

Project pakai simple conventional prefix.

~~~text
feat:
fix:
docs:
refactor:
test:
ci:
chore:
~~~

Kenapa?

Supaya history readable.

Compare:

~~~text
update
fix
fix again
last fix
~~~

dengan:

~~~text
feat: add monitoring endpoint
fix: prevent future leakage
docs: expand Airflow tutorial
~~~

History kedua jauh lebih informative.

---

## Squash merge

Feature branch kadang punya banyak commit kecil.

~~~text
try 1
fix typo
fix test
fix import
~~~

Saat merge ke develop, squash bisa turn jadi satu logical commit.

Benefit: integration history lebih clean.

Tapi jangan blindly squash kalau commit history memang punya meaningful independent steps.

---

## Branch policy di CI

Project CI validate direction.

Expected:

~~~text
feature-ish branch
→ develop

develop
→ main
~~~

Kalau docs branch langsung PR ke main, policy fail.

Kenapa encode process di CI?

Karena documentation rule tanpa enforcement gampang dilanggar.

---

## Branch protection / ruleset

CI policy membantu, tapi GitHub repository idealnya juga punya protection.

Contoh:

- require PR,
- require CI,
- block direct push,
- restrict force push.

Ini beda dengan CI check.

CI bisa bilang “fail”, tapi admin permission bisa saja still override.

Ruleset memberi governance lebih kuat.

---

## Rewriting history

Project pernah rewrite history sekali saat cleanup besar.

Itu okay **sebelum** workflow stabil dan kalau coordinated.

Tapi setelah team collaboration jalan, force rewrite shared branch dangerous.

Rule sehat:

> Bersihkan history early; setelah stable, hindari rewriting main tanpa alasan sangat kuat.

---

## Checkpoint

1. Main, develop, feat punya role apa?
2. Kenapa feature nggak langsung main?
3. PR berguna buat apa selain merge?
4. Squash merge kapan useful?
5. CI branch policy beda apa dengan GitHub branch protection?
