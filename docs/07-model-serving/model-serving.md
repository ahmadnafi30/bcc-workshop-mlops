# Model Serving

## From model file to usable service

Training produces a model.

But another application cannot conveniently call:

~~~text
open this Python process
import sklearn
load this file
build the exact features
predict
~~~

for every request.

Model serving creates a stable interface around the model.

In this workshop, the interface is HTTP through FastAPI.

## Analogy: kitchen and waiter

The trained model is like the kitchen.

A customer should not walk into the kitchen and manually combine ingredients.

The waiter accepts a simple order:

~~~text
zone 161
target 18:00
~~~

The serving layer handles the internal details.

That is why our API request does **not** ask clients to provide lag_24h or rolling_mean_6h.

## Request contract

Client sends:

~~~json
{
  "zone_id": 161,
  "target_datetime": "2025-01-28T18:00:00"
}
~~~

Backend responsibilities:

1. validate the request;
2. load historical demand;
3. build online features;
4. resolve the champion model;
5. run prediction;
6. log prediction metadata;
7. return a response.

## Online feature construction

The model expects the same feature schema used during training.

For target 18:00:

~~~text
lag_1h
→ 17:00

lag_24h
→ yesterday 18:00

rolling_mean_3h
→ recent history ending before 18:00
~~~

The serving code never reads actual demand at the target hour.

This protects against leakage.

## Training-serving consistency

A common production failure is:

~~~text
training feature definition
≠
serving feature definition
~~~

Then a model can look excellent offline but receive different inputs online.

Our project keeps the feature contract explicit.

A larger production system might use a feature store, but the principle is the same:

> Training and serving must agree on feature meaning.

## Champion model

Serving does not hard-code:

~~~text
version 1
~~~

It asks MLflow Registry for:

~~~text
champion
~~~

This separates:

~~~text
application code
from
model promotion decision
~~~

## Loader cache

Querying Model Registry for every individual prediction would create unnecessary traffic.

The loader caches model metadata for a short interval.

It periodically checks whether champion changed.

If champion moves to a new version, the model can be reloaded.

## Prediction logging

A successful prediction is written to:

~~~text
data/monitoring/predictions.jsonl
~~~

We need this later because model accuracy cannot be calculated until actual demand exists.

Each log includes information such as:

- target time,
- zone,
- predicted count,
- model version,
- MLflow run ID,
- log time.

## Why JSONL?

JSON Lines stores one JSON object per line.

It is simple for append-only workshop logging:

~~~text
prediction 1
prediction 2
prediction 3
~~~

A larger production system might use a database, event stream, or data warehouse.

## Negative regression outputs

A regression model can mathematically return a negative number.

Taxi pickup count cannot be negative.

The serving layer clips the final prediction at zero.

That is a domain constraint applied after model inference.

## Serving is not deployment

Important distinction:

~~~text
serving
→ how predictions are exposed

deployment
→ how the serving application is placed into an environment
~~~

FastAPI handles serving.

Docker/GHCR are part of packaging and delivery.
