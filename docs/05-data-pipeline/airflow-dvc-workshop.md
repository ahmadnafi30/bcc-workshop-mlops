# Airflow + DVC: A Workflow We Can Explain

Zora needs to answer: **Which data produced this model?** and **Which task runs next?**

> DVC reproduces the data pipeline. Airflow coordinates its execution. MLflow records model experiments.

## 1. Read the workflow

~~~text
Daily demand files
    |
    +--> DVC: build_training_features
    |        data/features/training/taxi_demand_features.parquet
    |            |
    |        DVC: create_training_snapshot
    |        data/snapshots/training/taxi_demand_<cutoff>.parquet
    |            |
    |        Airflow: train_model --> register_candidate --> MLflow
    |
    +--> Airflow replay: operational features for serving/retraining
             data/features/taxi_demand_features.parquet
~~~

Training and replay features are separate files. Reproducing initial training therefore does not shorten the dataset used for serving after later replay days arrive.

## 2. Configure the training period

Open `params.json`:

~~~json
{
  "data": {
    "history_start": "2025-01-01",
    "training_cutoff": "2025-01-26"
  }
}
~~~

`history_start` includes warm-up history for lags and rolling features. `training_cutoff` is the last permitted day. With these defaults, model-ready rows start Jan 8; training ends Jan 21; the default five-day validation covers Jan 22–26.

JSON is a supported DVC parameter format. `${data.training_cutoff}` substitutes its value into commands/output names; `params` declares values that can invalidate a stage. [DVC parameter files](https://doc.dvc.org/user-guide/project-structure/dvcyaml-files)

## 3. DVC hands-on

Run from the repository root after bootstrap/aggregation has created the daily demand history:

~~~powershell
uv run dvc dag
uv run dvc status
uv run dvc repro --dry create_training_snapshot
uv run dvc repro create_training_snapshot
uv run dvc status
~~~

| Command | What participants should explain |
| --- | --- |
| `dvc dag` | Features are an upstream dependency of the snapshot |
| `dvc status` | Checks current declared dependencies and outputs against recorded state |
| `dvc repro --dry ...` | Shows planned work without running stage commands |
| `dvc repro create_training_snapshot` | Reproduces the target and required upstream stages |
| Repeat `dvc repro ...` | Unchanged stages can be skipped or restored from cache |

| File / field | Purpose |
| --- | --- |
| `params.json` | Editable training dates |
| `dvc.yaml` | Recipe: command, dependencies, parameters, outputs |
| `dvc.lock` | Actual commands, parameter values, and content hashes |
| `.dvc/cache` | Local artifact objects indexed by content hash |
| `cmd` | How to create an output |
| `deps` | Input files and code that affect it |
| `params` | Configuration values that affect the stage |
| `outs` | Generated artifacts DVC tracks and caches |

The demand directory is a broad dependency. A later day can trigger the training-features stage, even after the cutoff. Its command still uses the configured date range; unchanged output content lets the snapshot remain unchanged. This simple declaration trades some unnecessary upstream work for readability.

### Make a new data version

If daily demand through Jan 28 is available:

1. Change `training_cutoff` in `params.json` to `2025-01-28`.
2. Run `uv run dvc repro create_training_snapshot`.
3. Inspect the new snapshot filename and lock changes.
4. Run `uv run python scripts/train_with_mlflow.py` to train using the configured snapshot. Its default follows `params.json`.

After reviewing the changes, these commands record the metadata in Git:

~~~powershell
git add params.json dvc.yaml dvc.lock
git commit -m "Record training snapshot through January 28"
~~~

This is an example for the participant to perform, not a command to commit all local files. Git stores metadata/code; DVC stores data objects in cache. A date alone does not guarantee identical data, so record hashes too.

For an older version, select its reviewed Git revision and use `dvc checkout` or `dvc repro`. Checkout needs the objects in cache/remote; reproduction needs the original dependencies/code. Save local work before switching Git revisions.

**Remote limitation:** no DVC remote is configured. `dvc push`/`dvc pull` need a remote first. A local cache is not an off-device backup.

## 4. Airflow hands-on

On Windows, use the Linux container with Docker Desktop running. If a Python MLflow server already occupies port 5000, stop that server before starting Compose MLflow; both use the same port/state folder.

~~~powershell
docker compose up -d --build mlflow airflow
docker compose ps
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags list-import-errors --output json
docker compose exec airflow airflow pools list
~~~

| Command | Purpose |
| --- | --- |
| `up -d --build mlflow airflow` | Updates the affected images and starts the services |
| `ps` | Shows state and host ports |
| `dags list` | Lists available workflows |
| `list-import-errors` | Lists files Airflow could not load |
| `pools list` | Shows the one-slot `taxi_workshop` pool |

DAG files are mounted read-only for live discovery. Business logic in `src/` is packaged into the image, so its changes need an image rebuild.

| DAG | Task flow | Prerequisite |
| --- | --- | --- |
| `taxi_initial_training` | create_snapshot → train_model → register_candidate | Complete initial demand history |
| `taxi_daily_replay` | get_replay_date → release_batch → validate_batch → aggregate_demand → rebuild_features | Prepared source and a replay_date such as Jan 27 |
| `taxi_model_monitoring` | evaluate_model → maybe_retrain | Champion, prediction log, and actual demand |

Initial training calls DVC and passes snapshot name/SHA256 to the training task. That task checks the same snapshot before fitting. Registration uses the existing baseline gate and produces a challenger.

Replay features use the latest available demand day. Replaying Jan 27 after Jan 28 does not remove Jan 28 from serving features. `status=cached` means input/range/code/output checks match; `status=rebuilt` means features were regenerated.

Monitoring compares recent MAE with the champion's reference validation MAE. `status=not_needed` can be a successful decision; it does not prove every kind of drift is absent.

### UI tour

1. Open the Airflow host port shown by `docker compose ps`, then **DAGs**. Use credentials for that instance, not an assumed `admin/admin`.
2. Open a DAG and choose **Trigger**. For replay, fill `replay_date` in the parameter form.
3. **Graph** explains dependency arrows. **Grid / run details** shows task state.
4. Select a task and open **Logs** for DVC output, feature cache status, and exceptions.
5. **XCom / task output** contains small metadata: date, path, rows, SHA256. DataFrames stay in the shared volume.
6. Inspect **Admin → Pools** when available in the UI; `pools list` is the CLI alternative.

For the first demo, follow initial training, review/promote the model, replay a day, send predictions, then evaluate when actual demand is available. Keep generated credentials off public slides.

## 5. Explain the optimizations

| Change | Plain explanation |
| --- | --- |
| Imports inside tasks | Heavy libraries load when executing a task, not each time Airflow reads the DAG |
| `max_active_runs=1` | One active run of each taxi DAG |
| `max_active_tasks=1` | One active task within that DAG |
| `taxi_workshop`: one slot | Tasks from all three taxi DAGs share one slot, avoiding simultaneous shared-file work |
| Global parallelism: two | Limits local scheduled-task concurrency |
| One API worker and one parser | Fewer background processes on the laptop |
| Selected retries | Data/evaluation tasks get one extra attempt; training/registration do not automatically create duplicate runs/versions |
| Execution timeout | A task has a time budget |
| Atomic Parquet write | Publish the complete file only after writing finishes |
| Feature cache | Reuse output only when content, dates, code, and output checksum match |

The pool coordinates this Airflow instance, not unrelated host scripts or another installation. Run host scripts after taxi workflows finish. Shared local volumes and standalone Airflow suit the workshop; distributed production needs shared storage, a suitable metadata database, and stronger publication controls. [Airflow best practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)

## 6. Why keep manual scheduling?

`schedule=None` and `catchup=False` let participants choose a historical 2025 date deliberately. For a real deployment, first define data arrival, timezone, intervals, and retry behavior, then configure scheduling.

## Troubleshooting

| Symptom | First action |
| --- | --- |
| Docker pipe error | Start Docker Desktop |
| DAG absent | Check import errors and the running image |
| Task waits for a pool | Check slots; another taxi task may be using the slot |
| Pool absent | Restart updated Airflow; the startup helper creates it |
| Missing daily demand | Prepare consecutive dates so lag history is valid |
| Snapshot hash mismatch | Inspect concurrent writes and reproduce a consistent snapshot |
| DVC up to date / feature cached | Expected when freshness checks pass |
| Model task failed | Read Logs before rerunning; do not delete state volumes |

## Ten-minute presentation

1. One minute: DVC's recipe and Airflow's execution order.
2. Three minutes: open params/recipe/lock, reproduce, and repeat to show cache.
3. Three minutes: trigger initial training and show Graph, Logs, and XCom.
4. Two minutes: open its MLflow run and snapshot fingerprint.
5. One minute: explain why successful tasks do not automatically make a model production-ready.
