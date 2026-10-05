# Retraining — Kapan Model Harus Belajar Lagi?

“Retrain model setiap hari” kedengarannya automation banget.

Tapi apakah selalu masuk akal?

Belum tentu.

Retraining punya cost:

- compute,
- time,
- experiment noise,
- validation effort,
- governance risk.

Jadi pertanyaan yang lebih sehat:

> **Evidence apa yang bikin kita percaya model perlu candidate baru?**

Workshop kita pakai performance degradation.

---

## Decision rule

Default:

~~~text
recent MAE
>
champion validation MAE × 1.25
~~~

dan:

~~~text
evaluated predictions >= 100
~~~

Dua condition.

Kenapa?

Karena threshold doang tanpa sample count bisa overreact.

---

## Example

Champion validation:

~~~text
MAE = 10
~~~

Multiplier:

~~~text
1.25
~~~

Threshold:

~~~text
12.5
~~~

Recent MAE:

~~~text
13.4
~~~

Evaluated predictions:

~~~text
350
~~~

Condition terpenuhi.

Monitoring recommend retrain.

---

## Kalau recent MAE 13.4 tapi sample cuma 5?

No retraining recommendation.

Kenapa?

Five samples terlalu sedikit buat confident conclusion.

Automation yang mature nggak harus agresif.

Kadang best action adalah wait for more evidence.

---

## Monitoring DAG

~~~text
evaluate_model
      ↓
maybe_retrain
~~~

Kalau healthy:

~~~text
not_needed
~~~

Kalau degraded:

~~~text
latest evaluated date
↓
new snapshot
↓
train
↓
validation
↓
MLflow tracking
↓
candidate evaluation
↓
register challenger
~~~

---

## Kenapa snapshot baru?

Karena retraining harus punya frozen dataset identity.

Kita nggak mau run training dari moving “latest” file lalu kehilangan context.

Snapshot baru punya cutoff date dan fingerprint.

---

## Validation window ikut maju

Ini penting.

Initial model:

~~~text
older period
→ train

latest 5 days
→ validation
~~~

Saat snapshot maju ke February, validation juga maju.

Kenapa?

Kalau validation tetap stuck di January, kita cuma tahu model baru bagus di old period.

Retraining harus evaluate pada more recent holdout.

---

## Kenapa beat baseline dulu?

Candidate baru harus minimal justify complexity-nya terhadap naive rule.

Kalau retrained model kalah dari naive lag_24h:

> Kenapa kita register sebagai candidate?

Nggak ada alasan kuat.

---

## Automatic retraining ≠ automatic promotion

Ini governance boundary paling penting.

Project allow:

~~~text
monitoring
→ automatic retraining
→ automatic challenger
~~~

Tapi stop sebelum:

~~~text
challenger
→ champion
~~~

Kenapa?

Karena candidate bisa beat baseline tapi belum tentu better than current champion on every relevant dimension.

Kita mungkin mau inspect:

- validation MAE,
- recent production-like MAE,
- data period,
- anomaly,
- business constraint,
- regression risk.

---

## Manual promotion bukan anti-automation

Kadang orang mikir:

> “Kalau masih manual berarti belum MLOps.”

No.

Automation level harus sesuai risk dan governance.

High-risk action bisa intentionally require approval.

MLOps bukan goal “semua harus auto”.

Goal-nya reliable lifecycle.

---

## Retraining vs continual learning

Retraining workshop kita adalah batch retraining.

~~~text
new snapshot
↓
train new model
~~~

Continual/online learning beda.

Model parameter update incrementally seiring data datang.

Jangan pakai istilah interchangeable.

---

## Setelah champion berubah

Serving layer resolve champion alias.

Loader akan detect version change setelah refresh interval.

Jadi lifecycle:

~~~text
new champion
↓
serving detects alias change
↓
reload model
↓
future predictions use new version
~~~

Application source code nggak perlu hard-code version baru.

---

## Closed loop

Sekarang lifecycle lengkap:

~~~text
serve
↓
observe
↓
evaluate
↓
degradation?
↓
retrain
↓
challenger
↓
review
↓
promote
↓
serve again
~~~

Ini salah satu core outcome workshop.

---

## Checkpoint

1. Kenapa nggak retrain tiap hari aja?
2. Kenapa minimum samples penting?
3. Kenapa validation window harus ikut maju?
4. Kenapa retrained model harus compare baseline?
5. Automatic retraining beda apa dengan automatic promotion?
6. Batch retraining beda apa dengan continual learning?
