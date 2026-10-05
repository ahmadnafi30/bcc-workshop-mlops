# Data Pipeline — Bootstrap & Replay: Dari Official Data ke Production-like Daily Batch

Bagian ini connect dataset concept dengan actual implementation.

Kita punya official monthly TLC data.

Tapi production-like pipeline kita ingin menerima data gradually.

Jadi kita butuh beberapa phase:

~~~text
download
↓
compact replay source
↓
release one logical day
↓
validate
↓
aggregate
~~~

---

## Bootstrap bukan production ingestion

Bootstrap adalah initial preparation.

Kita download historical dataset upfront karena workshop tidak bisa menunggu data real datang selama berminggu-minggu.

Command:

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Output source:

~~~text
data/source/tlc/
~~~

Output compact:

~~~text
data/source/replay/
~~~

---

## Kenapa replay source compact?

Official monthly TLC punya banyak columns.

Core use case cuma perlu:

~~~text
pickup datetime
pickup location
~~~

Kalau setiap daily simulation harus scan full source dengan semua columns, wasteful.

Jadi replay preparation:

~~~text
official file
↓
select fields
↓
filter Manhattan
↓
validate month
↓
compact parquet
~~~

---

## Release daily batch

Script:

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Concept:

~~~text
monthly replay source
↓
filter one date
↓
data/raw/trips/2025-01-27.parquet
~~~

Sekarang downstream cuma melihat logical day tersebut.

---

## Validation

Daily batch harus dicek sebelum processing.

Kita validate:

- file tidak empty,
- timestamp parseable,
- date sesuai requested logical date,
- pickup location available.

Kenapa validate date?

Bayangin file Jan 27 accidentally berisi Jan 28.

Kalau langsung aggregate, future data leak masuk history.

Data quality issue bisa berubah jadi modeling issue.

---

## Aggregate

Daily trip events jadi demand grid.

~~~text
trip rows
↓
group by hour + zone
↓
fill zero-demand combinations
↓
processed demand parquet
~~~

Output:

~~~text
data/processed/demand/YYYY-MM-DD.parquet
~~~

---

## Initial historical demand

Kita punya special initial preparation:

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

Kenapa nggak replay Jan 1 sampai 26 manual satu-satu?

Bisa.

Tapi workshop bakal habis waktu click run 26 kali.

Initial history adalah bootstrap state.

Production simulation mulai setelah model established.

---

## Daily replay dan idempotency

Suppose Jan 27 task run dua kali.

Ideal outcome sama.

Kalau second run append duplicate trips, monitoring dan features rusak.

Makanya output generated deterministically per logical date.

Idempotency bikin retries safe.

---

## Why file partition per day?

Per-day file bikin:

- logical boundaries jelas,
- replay mudah,
- ground truth lookup mudah,
- task input/output mudah dijelaskan.

Production could use partitioned object store/table, tapi concept sama.

---

## Common failure

### Missing replay source

Bootstrap belum selesai.

### Date out of source range

Requested date nggak ada.

### Empty Manhattan batch

Could indicate source/filter bug.

### Wrong schema

External source changed atau corrupt.

Fail early.

---

## Checkpoint

Coba trace Jan 27:

~~~text
official monthly file
→ replay monthly file
→ raw daily trip
→ processed daily demand
~~~

Kalau masing-masing role jelas, next feature pipeline gampang.
