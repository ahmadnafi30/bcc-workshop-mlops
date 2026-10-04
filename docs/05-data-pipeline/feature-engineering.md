# Feature Engineering Pipeline

## Goal

Convert processed hourly demand into model-ready rows.

Input:

~~~text
timestamp
zone_id
trip_count
~~~

Output includes:

~~~text
calendar features
lag features
rolling features
target_trip_count
~~~

## Run

~~~bash
uv run python scripts/build_features.py
~~~

Default output:

~~~text
data/features/taxi_demand_features.parquet
~~~

## Calendar features

From timestamp:

~~~text
hour
day_of_week
is_weekend
~~~

## Lag features

Created per zone:

~~~text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
~~~

Important phrase:

> **per zone**

We must not shift the entire table without grouping, because demand from one taxi zone must never become a lag for another zone.

## Rolling features

Also per zone:

~~~text
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Implementation uses a one-hour shift before rolling.

That enforces:

~~~text
target hour
is never inside
its own historical feature
~~~

## Sorting matters

Before shift/rolling:

~~~text
sort by zone_id, timestamp
~~~

Time-series operations assume rows are in the correct order.

If the data is shuffled, shift can silently create nonsense.

## Drop incomplete rows

The longest lag needs 168 hours.

Rows without complete model features are removed from the final model-ready dataset.

That is why the first week acts as history.

## Leakage checklist

For a target time t:

- calendar info at t: allowed;
- demand at t - 1h: allowed;
- demand at t - 24h: allowed;
- rolling window ending at t - 1h: allowed;
- actual demand at t: target only, never a feature;
- future demand: forbidden.

## Why one feature function for training?

Training and serving must agree on feature definitions.

This project has separate batch and online construction paths, but they follow the same feature contract.

That concept is called **training-serving consistency**.

A production feature store is one way larger systems manage that problem. We keep it explicit in Python for learning.
