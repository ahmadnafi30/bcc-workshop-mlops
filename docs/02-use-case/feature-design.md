# Feature & Model Design

## From demand to features

After aggregation:

| timestamp | zone_id | trip_count |
| --- | ---: | ---: |
| 17:00 | 161 | 142 |
| 18:00 | 161 | 165 |

For the 18:00 row:

~~~text
target_trip_count = 165
~~~

Every predictive feature must come from information available before 18:00.

## Calendar features

~~~text
hour
day_of_week
is_weekend
~~~

Taxi demand at Monday 08:00 can look very different from Saturday 23:00.

## Lag features

~~~text
lag_1h
lag_2h
lag_3h
lag_24h
lag_168h
~~~

For target 18:00:

~~~text
lag_1h   = 17:00
lag_24h  = yesterday 18:00
lag_168h = one week ago 18:00
~~~

Analogy:

> To guess how busy a cafe will be at 18:00, you might ask how busy it is now, yesterday at 18:00, and last week at 18:00.

## Rolling features

~~~text
rolling_mean_3h
rolling_mean_6h
rolling_mean_24h
~~~

Important:

~~~text
shift first
then rolling
~~~

If the target is 18:00, the rolling window must end before 18:00.

Otherwise the feature contains part of the answer.

## Warm-up period

The longest lag is 168 hours, or one week.

Therefore the first seven days only provide history.

~~~text
Jan 1–7
warm-up

Jan 8 onward
complete training rows
~~~

## Zero-demand rows

A zone with zero pickups still has meaningful demand: zero.

So aggregation creates every combination:

~~~text
24 hours × all Manhattan zones
~~~

and fills missing counts with zero.

That keeps each zone's hourly time series continuous.

## Main model

We use scikit-learn:

~~~text
HistGradientBoostingRegressor
~~~

Why:

- strong tabular baseline,
- fast,
- CPU-friendly,
- easy to package,
- no GPU needed,
- supports categorical features.

Zone ID is categorical because ID 200 is not mathematically larger than ID 100 in a meaningful way.

## Baseline

~~~text
prediction = lag_24h
~~~

The ML model must beat this simple rule on MAE.

## Time-based validation

Initial snapshot:

~~~text
Jan 8–21  training
Jan 22–26 validation
~~~

We do not use a random split because future and past should not be mixed arbitrarily.

For retraining, validation becomes the last five days of the latest snapshot.

## Why not LSTM or Chronos?

Those can be good advanced experiments.

The core workshop keeps the model simple so the MLOps lifecycle stays visible.
