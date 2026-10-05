# Problem Statement

## Prediction target

We predict:

> **the number of Yellow Taxi pickups in one Manhattan taxi zone for one target hour.**

Example:

~~~text
target:
zone 161 at 18:00

output:
predicted_trip_count
~~~

## What information is allowed?

For target 18:00, the model may use:

- demand at 17:00,
- demand at 16:00,
- yesterday at 18:00,
- last week at 18:00,
- recent rolling averages,
- hour and weekday.

It may **not** use actual 18:00 demand.

That would be leakage.

## Raw vs model granularity

Raw:

~~~text
one row = one taxi trip
~~~

Model:

~~~text
one row = one zone × one hour
~~~

Example aggregation:

| pickup time | zone |
| --- | ---: |
| 17:03 | 161 |
| 17:10 | 161 |
| 17:44 | 162 |

becomes:

| timestamp | zone_id | trip_count |
| --- | ---: | ---: |
| 17:00 | 161 | 2 |
| 17:00 | 162 | 1 |

## Scope

Core workshop:

- Yellow Taxi,
- Manhattan pickup zones,
- early 2025 historical data,
- one-hour forecast horizon,
- pickup count target.

## Metrics

Primary:

~~~text
MAE
~~~

MAE 10 means the model is wrong by around 10 pickups per zone-hour on average.

Secondary:

~~~text
RMSE
~~~

RMSE reacts more strongly to large errors.

## Baseline

Our naive baseline is:

~~~text
prediction(t) = demand(t - 24 hours)
~~~

In plain language:

> Use the same hour yesterday.

A more complicated model should beat this baseline before its complexity feels justified.

## Why this is good for MLOps

A normal assignment might stop after train + evaluate.

This project continues into:

~~~text
tracking
registry
serving
monitoring
retraining
~~~

That continuation is the important part.
