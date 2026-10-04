# Dataset

## Main source

We use official **NYC TLC Yellow Taxi Trip Records**.

Raw fields we care about:

~~~text
tpep_pickup_datetime
PULocationID
~~~

Taxi zone lookup fields:

~~~text
LocationID
Borough
Zone
~~~

## Why does the base URL show AccessDenied?

If you open the CloudFront directory URL directly, you may see an XML AccessDenied response.

That does not mean the data files are blocked.

The storage endpoint simply does not provide public directory listing.

Known object paths work, for example:

~~~text
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet
~~~

Our bootstrap code builds the exact monthly object path automatically.

Mental model:

~~~text
browse folder
❌

request exact known file
✅
~~~

## Bootstrap flow

~~~bash
uv run python scripts/bootstrap_data.py
~~~

The script:

1. downloads taxi zone metadata;
2. downloads monthly Yellow Taxi Parquet;
3. keeps the useful columns;
4. filters Manhattan pickup zones;
5. removes rows outside the expected month;
6. creates a smaller replay source.

Folders:

~~~text
data/source/tlc
data/source/replay
data/metadata
~~~

## Why Parquet?

Parquet is columnar.

We can read only the columns we need instead of loading the entire source schema.

That saves I/O and memory.

## Why source and replay are separate

~~~text
official file
    ↓
select useful columns
    ↓
filter Manhattan
    ↓
compact replay file
~~~

The source is the original package. Replay is the workshop-ready version.

## Optional weather

The full workshop works with TLC data alone.

Later, weather can enrich features such as:

- temperature,
- rainfall,
- snowfall,
- wind speed.

~~~text
Taxi Data ─────┐
               ├── Feature Engineering
Weather Data ──┘
~~~

Weather is an extension, not a requirement.

## Git and generated data

Generated data is ignored by Git.

Git should track the code that creates the data, while DVC later helps track training snapshots.

## Timezone simplification

The workshop treats pickup timestamps as naive NYC local wall-clock time.

For the main hands-on period around January and February, this keeps the explanation simple.

A production design should explicitly handle timezone and daylight-saving transitions.
