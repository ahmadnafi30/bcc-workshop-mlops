# Step 1 — Data Bootstrap

## Goal

Prepare a compact local copy of NYC TLC data that can be replayed like incoming production data.

## Mental model

We have two forms:

~~~text
official source
→ original package

replay source
→ smaller workshop-ready package
~~~

We keep both roles separate.

## 1. Bootstrap

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Default behavior prepares the configured 2025 months.

This can take time because official monthly Parquet files are large.

## 2. What the script does

~~~text
download taxi zone lookup
       ↓
download Yellow Taxi month
       ↓
read pickup time + pickup zone
       ↓
filter Manhattan
       ↓
validate expected month
       ↓
write compact replay parquet
~~~

## 3. Inspect folders

After a successful bootstrap:

~~~text
data/
├── metadata/
│   └── taxi_zone_lookup.csv
└── source/
    ├── tlc/
    │   └── yellow_tripdata_....parquet
    └── replay/
        └── yellow_tripdata_....parquet
~~~

These files are ignored by Git.

## 4. Why the CloudFront directory is AccessDenied

If you open the base trip-data URL and see AccessDenied, that does not mean the monthly file is inaccessible.

The storage does not expose a directory listing.

The code requests an exact file name.

## 5. Optional notebook exploration

~~~bash
uv run jupyter lab
~~~

Open:

~~~text
notebooks/01-data-exploration.ipynb
~~~

Questions to answer:

- How many rows are in the replay source?
- How many pickup zones remain?
- What is the time range?
- Are timestamps missing?
- Which zones have many pickups?

Do not spend the whole workshop doing EDA. The notebook is a sanity check.

## 6. Prepare initial history

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

This prepares Jan 1–26 by default.

Output pattern:

~~~text
data/processed/demand/2025-01-01.parquet
...
data/processed/demand/2025-01-26.parquet
~~~

## 7. Why one file per day?

It matches the replay story.

Later Airflow can process:

~~~text
Jan 27 batch
Jan 28 batch
Jan 29 batch
~~~

without pretending all production data arrived at once.

## Checkpoint

Verify one file exists:

~~~text
data/processed/demand/2025-01-26.parquet
~~~

If it does, continue to feature engineering.
