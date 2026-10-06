# Step 1 — Data: Dari Official TLC Sampai Hourly Demand yang Siap Dipakai

Hi peers, sekarang kita mulai pegang data beneran.

Sebelum masuk model, kita perlu memastikan satu hal penting:

> “Kita sebenarnya sedang memprediksi dari data seperti apa?”

Karena salah satu mistake paling common di ML adalah terlalu cepat ngomongin model padahal data lifecycle-nya belum jelas.

Di step ini kita akan:

1. download official NYC TLC data;
2. prepare replay source;
3. inspect data;
4. prepare initial hourly demand history;
5. ngerti kenapa folder data dipisah;
6. ngerti apa yang nanti direplay oleh Airflow.

---

## Goal

Setelah selesai, kalian harus bisa menjawab:

- raw TLC row artinya apa;
- kenapa kita fokus Manhattan;
- kenapa replay source dibuat compact;
- bedanya source, raw, processed;
- kenapa hourly demand perlu complete grid;
- kenapa Jan 1–26 disiapkan di awal;
- apa role warm-up Jan 1–7;
- bagaimana data ini nanti dipakai model dan monitoring.

Kalau cuma berhasil download file tapi nggak bisa jawab pertanyaan itu, step ini belum benar-benar selesai.

---

## 1. Sebelum download, lihat problem-nya dulu

Use case kita:

> Predict jumlah pickup taxi per Manhattan zone satu jam ke depan.

Raw TLC data punya:

~~~text
one row
=
one taxi trip
~~~

Model kita butuh:

~~~text
one row
=
one zone × one hour
~~~

Artinya data tidak bisa langsung masuk model.

Ada transformation lifecycle.

---

## 2. Bootstrap official dataset

Setelah step ini:

- official taxi data ter-download,
- zone lookup tersedia,
- replay source terbentuk,
- initial historical demand Jan 1–26 siap,
- kalian ngerti raw granularity vs model granularity.

---

### Sebelum membuka dokumentasi dataset

Raw TLC punya satu row per trip.

Coba jawab:

> “Kalau target kita jumlah pickup per zone per jam, apakah model perlu satu row per individual trip?”

No.

Kita akan aggregate.

Tapi raw source tetap penting sebagai starting point.

---

### Jalankan bootstrap

~~~bash
uv run python scripts/bootstrap_data.py
~~~

First run bisa lumayan lama karena monthly TLC Parquet cukup besar.

Jangan panik kalau terminal kelihatan sibuk.

---

## 3. Apa yang sebenarnya didownload?

Dua hal utama.

### Yellow Taxi monthly Parquet

Contoh:

~~~text
yellow_tripdata_2025-01.parquet
~~~

### Taxi Zone Lookup

Mapping:

~~~text
LocationID
→ Borough
→ Zone
~~~

Tanpa lookup, PULocationID hanya angka.

Kita butuh tahu mana zone Manhattan.

---

## 4. Kenapa base CloudFront URL bisa AccessDenied?

Kalau kalian coba buka folder base URL dan dapat XML AccessDenied, itu normal.

Object storage-nya tidak expose directory listing.

Mental model:

~~~text
browse folder
❌

request exact known object
✅
~~~

Script bootstrap tahu exact monthly object URL.

Jadi AccessDenied di prefix bukan berarti dataset private.

---

## 5. Lihat folder setelah bootstrap

Expected:

~~~text
data/
├── metadata/
│   └── taxi_zone_lookup.csv
└── source/
    ├── tlc/
    │   └── yellow_tripdata_2025-01.parquet
    └── replay/
        └── yellow_tripdata_2025-01.parquet
~~~

Question:

> “Kenapa TLC source dan replay source dua-duanya disimpan?”

Karena responsibility beda.

~~~text
tlc/
→ original downloaded source

replay/
→ compact workshop-ready historical source
~~~

---

## 6. Kenapa replay source lebih kecil?

Original TLC punya banyak columns.

Core use case kita terutama butuh:

~~~text
tpep_pickup_datetime
PULocationID
~~~

Kita filter Manhattan juga.

Jadi replay source lebih kecil dan cepat dibaca ulang.

Ini penting karena historical simulation akan sering access data tersebut.

---

## 7. Inspect metadata zone lookup

Try:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_csv('data/metadata/taxi_zone_lookup.csv'); print(df.head()); print(df[df['Borough']=='Manhattan'].head())"
~~~

Coba jawab:

- LocationID itu apa?
- Borough dipakai buat apa?
- Zone name useful buat apa?

Model pakai zone_id, tapi human debugging sering terbantu zone name.

---

## 8. Optional notebook exploration

Run:

~~~bash
uv run jupyter lab
~~~

Open notebook exploration.

~~~text
notebooks/01-data-exploration.ipynb
~~~

Jangan treat notebook sebagai mandatory full EDA project.

Kita cuma sanity check:

- row count;
- date range;
- missing values;
- pickup zones;
- top pickup zones;
- sample hourly aggregation.

Question:

> “Apakah source yang kita download masuk akal sebelum masuk pipeline?”

---

## 9. Prepare initial historical demand

Run:

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

Default range:

~~~text
2025-01-01
through
2025-01-26
~~~

Output:

~~~text
data/processed/demand/2025-01-01.parquet
...
data/processed/demand/2025-01-26.parquet
~~~

---

## 10. Kenapa Jan 1–26?

Karena kita butuh tiga logical segments.

~~~text
Jan 1–7
→ warm-up history

Jan 8–21
→ training

Jan 22–26
→ validation
~~~

Lag terpanjang:

~~~text
168h = 7 days
~~~

Makanya Jan 8 adalah titik pertama yang punya one-week history lengkap.

---

## 11. Warm-up bukan wasted data

Jan 1–7 memang tidak jadi target training rows complete.

Tapi dia menyediakan context untuk:

~~~text
lag_168h
rolling windows
recent history
~~~

Analoginya:

> Kalian mungkin nggak menilai siswa dari minggu orientasi, tapi aktivitas minggu orientasi bisa jadi context buat minggu berikutnya.

Data yang tidak jadi target row tetap bisa useful sebagai history.

---

## 12. Inspect satu processed day

Try:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/processed/demand/2025-01-26.parquet'); print(df.head()); print(df.shape); print(df['timestamp'].min(), df['timestamp'].max())"
~~~

Expected columns:

~~~text
timestamp
zone_id
trip_count
~~~

---

## 13. Kenapa processed row count bukan raw row count?

Raw:

~~~text
one trip
→ one row
~~~

Processed:

~~~text
one zone-hour
→ one row
~~~

Jadi jutaan trip bisa jadi jauh lebih sedikit hourly rows.

Aggregation memang mengubah granularity.

---

## 14. Complete grid sanity check

Suppose Manhattan punya Z zones.

One day expected:

~~~text
24 × Z rows
~~~

Kenapa?

Setiap zone harus punya semua jam.

Termasuk jam tanpa pickup.

---

## 15. Zero demand vs missing data

Ini distinction important.

No trip di zone tertentu jam 03:00:

~~~text
trip_count = 0
~~~

Bukan:

~~~text
row missing
~~~

Missing row bisa berarti data pipeline gagal.

Zero berarti observed demand memang nol.

Kalau semantics ini salah, lag feature nanti juga salah.

---

## 16. Total pickup sanity

Optional:

~~~bash
uv run python -c "import pandas as pd; df=pd.read_parquet('data/processed/demand/2025-01-26.parquet'); print(df['trip_count'].sum())"
~~~

Compare roughly dengan trip count source Manhattan hari itu kalau ingin.

Goal:

> processed aggregation tidak tiba-tiba double atau kehilangan massive rows.

---

## 17. Kenapa data tidak di-commit ke Git?

Generated Parquet cukup besar dan berubah.

Git cocok buat:

- code;
- config;
- docs;
- DAG.

Generated data punya lifecycle lain.

Nanti DVC membantu snapshot reproducibility.

---

## 18. Predict apa yang akan terjadi di Jan 27

Sekarang kita punya history sampai Jan 26.

Production-like period dimulai Jan 27.

Kalau kita release Jan 27 nanti:

~~~text
replay monthly source
↓
raw Jan 27
↓
processed Jan 27
↓
features extend
~~~

Coba visualize ini sebelum Airflow masuk.

---

## 19. Manual release Jan 27 — optional preview

Kalau mau lihat:

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Lalu:

~~~bash
uv run python scripts/prepare_daily_demand.py --date 2025-01-27
~~~

Kita nanti ulang concept yang sama via Airflow.

Kenapa manual dulu?

Karena kalau Airflow gagal, kalian tahu underlying operation-nya apa.

---

## 20. Common issue: file sudah ada

Downloader bisa skip file existing.

Ini useful supaya rerun bootstrap nggak download semua dari nol.

Tapi kalau kalian curiga local file corrupt, jangan assume skip = valid.

Inspect/remove intentionally lalu redownload.

Idempotency dan caching harus tetap punya integrity check mindset.

---

## 21. Common issue: disk space

Monthly TLC files besar.

Workshop presenter sebaiknya pre-download sebelum hari H.

Participant juga perlu cukup disk space.

Kalau download fail random, cek disk sebelum debugging Python logic terlalu jauh.

---

## 22. Common issue: internet venue

Ini alasan presenter checklist nanti menyarankan pre-bootstrap data.

Workshop objective bukan menguji Wi-Fi.

Source data bisa disiapkan sebelum session supaya waktu lebih banyak buat MLOps.

---

## 23. Mini challenge

Coba jawab:

### Tiga contoh baris pickup

~~~text
17:03 — Zone 161
17:10 — Zone 161
17:44 — Zone 162
~~~

Setelah hourly aggregation:

~~~text
17:00 zone 161 → ?
17:00 zone 162 → ?
~~~

Answer:

~~~text
2
1
~~~

Simple, tapi ini transformation fundamental seluruh project.

---

## 24. Checkpoint

Sebelum Step 2, pastikan:

~~~text
data/metadata/taxi_zone_lookup.csv
✅

data/source/replay/...
✅

data/processed/demand/2025-01-26.parquet
✅
~~~

Dan coba explain:

1. Raw row artinya apa?
2. Model row nanti artinya apa?
3. Why Manhattan only?
4. Replay source beda apa dengan official source?
5. Processed demand beda apa dengan raw trips?
6. Kenapa zero demand perlu row explicit?
7. Jan 1–7 role-nya apa?
8. Jan 8–21 role-nya apa?
9. Jan 22–26 role-nya apa?
10. Kenapa Git nggak simpan generated Parquet?
11. Manual Jan 27 flow seperti apa?
12. Kalau row count processed tidak 24 × zones, apa yang kalian curigai?

Kalau jawabannya clear, kita siap masuk feature engineering + baseline model.
