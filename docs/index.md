# Welcome, peers 👋

Welcome to **BCC Workshop — MLOps**.

Presenters:

- **Ahmad Nafi Mubarok**
- **Fatoni Murfid Syafii**

If this is your first time hearing words such as DVC, DAG, Model Registry, container, CI/CD, Prometheus, or retraining trigger, that is completely okay.

These docs assume you know basic Python and basic machine learning, but **do not assume prior MLOps experience**.

## The story

Imagine you trained a model in a notebook and got a good MAE.

Then someone asks:

> “Okay, how do we use this every day?”

Suddenly the questions become bigger:

- Which dataset produced the model?
- Which hyperparameters were used?
- Can another teammate reproduce it?
- Where is the approved model?
- How does an application request a prediction?
- What happens when the API becomes slow?
- What happens when the model becomes inaccurate?
- Who decides when to retrain?
- Which model version is serving right now?
- What happens after someone pushes new code?

That is where MLOps starts becoming useful.

## Our use case

We predict:

> **the number of NYC Yellow Taxi pickups for each Manhattan taxi zone one hour ahead.**

Raw source:

~~~text
one row = one taxi trip
~~~

Model dataset:

~~~text
one row = one taxi zone × one hour
~~~

Features include recent demand, yesterday's demand, weekly demand, rolling averages, hour, and weekday.

## Full lifecycle

~~~text
Official TLC data
       ↓
prepare history
       ↓
hourly zone demand
       ↓
feature engineering
       ↓
training snapshot
       ↓
baseline + ML model
       ↓
experiment tracking
       ↓
model registry
       ↓
orchestration
       ↓
prediction API
       ↓
containers
       ↓
CI/CD
       ↓
monitoring
       ↓
retraining decision
       ↓
challenger model
~~~

Do not memorize the diagram.

Keep asking:

> **What problem does this component solve?**

That question is the main learning method in this workshop.

## Recommended order

1. Workshop Overview
2. MLOps from Zero
3. Architecture
4. Git Workflow
5. Use Case
6. Tools and lifecycle sections
7. Hands-on Workshop

## One analogy we will reuse

Think of a machine learning model as a **recipe**.

A recipe alone is not a restaurant.

A restaurant still needs ingredients, inventory, a kitchen process, quality control, order handling, monitoring, and a way to improve the menu.

Same idea:

~~~text
model.py alone ≠ ML system
~~~

MLOps is the engineering around the model that makes the lifecycle repeatable and observable.
