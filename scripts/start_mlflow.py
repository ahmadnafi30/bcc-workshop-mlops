import os
from pathlib import Path
import subprocess


# start MLflow lokal dengan state folder yang sama seperti service Docker
def main() -> None:
    # satu state directory bikin experiment dan registry tetap ada saat pindah ke Compose
    root = Path(__file__).resolve().parents[1]
    state_dir = root / ".mlflow"
    artifact_dir = state_dir / "artifacts"
    port = os.getenv("MLFLOW_PORT", "5000")

    state_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    print(f"mlflow state: {state_dir}")
    print(f"mlflow ui: http://127.0.0.1:{port}")

    subprocess.run(
        [
            "mlflow",
            "server",
            "--host",
            "127.0.0.1",
            "--port",
            port,
            "--backend-store-uri",
            "sqlite:///.mlflow/mlflow.db",
            "--artifacts-destination",
            str(artifact_dir),
            "--serve-artifacts",
            "--allowed-hosts",
            f"127.0.0.1:{port},localhost:{port}",
        ],
        cwd=root,
        check=True,
    )


if __name__ == "__main__":
    main()
