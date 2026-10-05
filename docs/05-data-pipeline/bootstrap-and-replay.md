# Bootstrap & Historical Data Preparation

## Goal

At the end of this section, we want:

~~~text
official TLC source
      ↓
compact replay source
      ↓
initial hourly demand history
~~~

## Step 1 — bootstrap official data

~~~bash
uv run python scripts/bootstrap_data.py
~~~

Default months are configured in the script.

What happens:

1. download zone lookup;
2. download monthly Yellow Taxi Parquet;
3. validate month format;
4. read the useful columns;
5. filter Manhattan;
6. remove timestamps outside the month;
7. save compact replay data.

## Why validate external data?

Even official data is still external input.

A robust pipeline does not blindly assume every file has exactly the expected schema forever.

That is why ingestion code checks important columns and date ranges.

## Data folders

~~~text
data/
├── source/
│   ├── tlc/
│   └── replay/
└── metadata/
~~~

The original download and prepared replay data have different responsibilities.

## Step 2 — inspect the data

Optional notebook:

~~~text
notebooks/01-data-exploration.ipynb
~~~

Start Jupyter:

~~~bash
uv run jupyter lab
~~~

The notebook is intentionally lightweight.

We are checking:

- row count,
- time range,
- missing values,
- Manhattan zones,
- sample hourly aggregation.

This is a sanity check, not a full analytics project.

## Step 3 — prepare initial historical demand

~~~bash
uv run python scripts/prepare_historical_demand.py
~~~

Default range:

~~~text
2025-01-01
through
2025-01-26
~~~

Why this range?

~~~text
Jan 1–7
warm-up for lag_168h

Jan 8–21
training

Jan 22–26
validation
~~~

## Aggregation

The raw replay source still has one row per trip.

Aggregation creates:

~~~text
one row = one Manhattan zone × one hour
~~~

Output:

~~~text
data/processed/demand/YYYY-MM-DD.parquet
~~~

## Complete grid

A missing trip group is not the same thing as a missing time step.

If a zone has zero pickups, we still need:

~~~text
trip_count = 0
~~~

So the preprocessing code creates every hour × zone combination and fills missing counts with zero.

## Manual daily replay

Later, to simulate new data:

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
uv run python scripts/prepare_daily_demand.py --date 2025-01-27
~~~

This manual path is useful before we let Airflow orchestrate the same logic.

## Why learn the manual path first?

Because orchestration should not hide understanding.

If the Airflow task fails, you should still know what underlying command and data transformation it represents.
