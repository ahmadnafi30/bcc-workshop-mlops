# Historical Replay

## Why replay?

A real production system receives data gradually.

Our dataset is historical.

If we expose all future records immediately, the exercise no longer behaves like production.

So we reveal historical data one day at a time.

## Analogy

Imagine practicing live commentary using a recorded match.

You already have the recording, but you replay it minute by minute instead of jumping to the final score.

Same idea here.

## Replay source

Bootstrap prepares:

~~~text
data/source/replay/
├── yellow_tripdata_2025-01.parquet
├── yellow_tripdata_2025-02.parquet
└── ...
~~~

## Release one date

~~~bash
uv run python scripts/simulate_daily_data.py --date 2025-01-27
~~~

Output:

~~~text
data/raw/trips/2025-01-27.parquet
~~~

Now downstream steps act as if Jan 27 just arrived.

## Processed demand

That batch becomes:

~~~text
data/processed/demand/2025-01-27.parquet
~~~

with:

~~~text
one row = one zone × one hour
~~~

## Initial history

Before production replay we prepare:

~~~text
Jan 1–26
~~~

This covers:

- one-week feature warm-up,
- initial training,
- initial validation.

Then replay starts on Jan 27.

## Prediction timing

For target 18:00:

~~~text
before 18:00
make prediction

18:00–18:59
actual trips happen

afterward
ground truth is available
~~~

The online feature provider only reads historical timestamps before the target hour.

## Why replay is useful for monitoring

~~~text
prediction
   ↓
historical clock advances
   ↓
actual demand
   ↓
error
   ↓
monitoring
   ↓
retraining decision
~~~

We can demonstrate a multi-day lifecycle in a workshop without waiting multiple real days.

The clock is simulated; the dependency logic is real.
