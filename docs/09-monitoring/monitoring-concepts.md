# Monitoring — API Hijau Belum Berarti Modelnya Bagus

Ini bagian yang menurutku salah satu paling penting di whole workshop.

Karena banyak ML project berhenti di:

~~~text
model deployed
↓
done
~~~

Padahal justru setelah deployment kita masuk environment yang paling unpredictable: dunia nyata.

Model sekarang melihat data baru.

Kita butuh feedback.

---

## Dua health dimension

### System health

Pertanyaan:

~~~text
API hidup?
latency berapa?
error rate?
request rate?
service reachable?
~~~

### Model health

Pertanyaan:

~~~text
prediction masih akurat?
recent MAE naik?
model version mana?
perlu retrain?
~~~

Dua-duanya penting.

---

## Case A — service bagus, model jelek

~~~text
HTTP 200
latency 50 ms
zero error
~~~

Tapi:

~~~text
actual 200
prediction 80
~~~

berulang-ulang.

Prometheus operational dashboard bisa kelihatan green.

Tapi model clearly nggak trustworthy.

---

## Case B — model bagus, service jelek

Offline/recent model metric bagus.

Tapi API:

~~~text
latency 20 sec
timeouts
5xx
~~~

Model bagus, tapi user tetap nggak bisa pakai.

---

## Analogi restoran

Operational monitoring:

> “Restoran buka nggak? Pesanan datang cepat nggak?”

Model monitoring:

> “Makanannya masih enak nggak?”

Restoran bisa serve cepat tapi makanan jelek.

Bisa juga makanan enak tapi customer nunggu satu jam.

Health dimension berbeda.

---

## Delayed ground truth

Ini yang bikin ML monitoring unik.

Saat jam 17:00 kita predict demand jam 18:00:

~~~text
prediction exists
actual 18:00 belum complete
~~~

Ground truth datang kemudian.

Jadi flow:

~~~text
predict
↓
log prediction
↓
wait
↓
actual available
↓
join prediction + actual
↓
calculate error
~~~

Model performance monitoring naturally delayed.

---

## Prediction log

Kita simpan:

~~~text
data/monitoring/predictions.jsonl
~~~

Isi penting:

~~~text
logged_at
zone_id
target_datetime
prediction
model_version
run_id
~~~

Kenapa model_version dan run_id?

Supaya performance bisa di-attribusikan ke model yang benar.

Kalau champion berubah, kita nggak mau error lama dianggap berasal dari model baru.

---

## Evaluation table

Saat ground truth ada:

~~~text
prediction
+
actual
↓
absolute_error
squared_error
~~~

Disimpan ke evaluations parquet.

Sekarang kita punya evidence per prediction.

---

## Recent window

Kenapa nggak pakai all-time MAE?

Bayangin model sangat bagus selama 6 bulan, lalu minggu ini jelek.

All-time average bisa tetap kelihatan baik karena historical good performance mendominasi.

Kita lebih interested pada recent behavior.

Makanya ada recent window/limit.

---

## Reference MAE

Kita nggak hard-code:

~~~text
if MAE > 20
then retrain
~~~

Kenapa 20?

Arbitrary.

Kita anchor ke champion validation performance.

Example:

~~~text
reference MAE = 10
multiplier = 1.25
threshold = 12.5
~~~

Kalau recent MAE > 12.5 dan sample cukup, retrain recommended.

---

## Minimum samples

Satu weird prediction nggak cukup buat conclude model rusak.

Could be outlier.

Makanya ada minimum sample.

~~~text
min_samples = 100
~~~

Decision butuh enough evidence.

---

## Drift vs degradation

Jangan campur.

### Data drift

Input distribution berubah.

### Performance degradation

Prediction error memburuk.

Drift bisa terjadi tanpa accuracy drop.

Accuracy drop juga bisa terjadi tanpa simple drift indicator.

Workshop monitor performance karena ground truth tersedia.

Evidently atau dedicated drift monitoring bisa jadi extension.

---

## Monitoring should lead to action

Dashboard cantik tapi nggak ada decision process kurang meaningful.

Project kita expose:

~~~text
retrain_recommended
~~~

Airflow monitoring DAG consume decision tersebut.

Jadi feedback loop benar-benar connect ke action.

---

## Checkpoint

1. System health beda apa dengan model health?
2. Kenapa ground truth delayed?
3. Kenapa prediction harus dilog?
4. Kenapa recent window lebih useful daripada all-time?
5. Kenapa threshold relative ke champion?
6. Drift dan degradation beda apa?
