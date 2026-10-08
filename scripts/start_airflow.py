import os
import subprocess
from pathlib import Path


# start Airflow standalone dengan DAG folder project ini tanpa setup path manual
def main() -> None:
    # environment dibuat dari current shell lalu diisi default khusus workshop
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("AIRFLOW_HOME", str(root / ".airflow"))
    env.setdefault(
        "AIRFLOW__CORE__DAGS_FOLDER",
        str(root / "dags"),
    )
    # Sembunyikan DAG demo bawaan agar peserta fokus pada workflow taxi.
    env.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "false")
    # Small limits keep a workshop laptop responsive; override via environment if needed.
    env.setdefault("AIRFLOW__CORE__PARALLELISM", "2")
    env.setdefault("AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG", "1")
    env.setdefault("AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG", "1")
    env.setdefault("AIRFLOW__DAG_PROCESSOR__PARSING_PROCESSES", "1")
    env.setdefault("AIRFLOW__API__WORKERS", "1")

    print(f"airflow home: {env['AIRFLOW_HOME']}")
    print(f"dags folder: {env['AIRFLOW__CORE__DAGS_FOLDER']}")
    print("taxi_workshop pool: 1 task taxi pada satu waktu")

    # The pool must exist before any taxi task can be scheduled. Setup is repeatable.
    subprocess.run(["airflow", "db", "migrate"], cwd=root, env=env, check=True)
    subprocess.run(
        [
            "airflow",
            "pools",
            "set",
            "taxi_workshop",
            "1",
            "One taxi task at a time: shared files and CPU-friendly training",
        ],
        cwd=root,
        env=env,
        check=True,
    )

    # standalone start API server, scheduler, database, dan local auth buat demo
    subprocess.run(
        ["airflow", "standalone"],
        cwd=root,
        env=env,
        check=True,
    )


if __name__ == "__main__":
    main()
