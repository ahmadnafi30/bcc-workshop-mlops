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

    print(f"airflow home: {env['AIRFLOW_HOME']}")
    print(f"dags folder: {env['AIRFLOW__CORE__DAGS_FOLDER']}")

    # standalone start API server, scheduler, database, dan local auth buat demo
    subprocess.run(
        ["airflow", "standalone"],
        cwd=root,
        env=env,
        check=True,
    )


if __name__ == "__main__":
    main()
