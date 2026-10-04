from pathlib import Path

from training.experiment import run_mlflow_experiment


# train baseline dan model utama lalu kirim result plus dataset fingerprint ke MLflow
def main() -> None:
    # training script sekarang reuse function yang sama dengan Airflow task
    root = Path(__file__).resolve().parents[1]
    snapshot_path = (
        root
        / "data"
        / "snapshots"
        / "training"
        / "taxi_demand_2025-01-26.parquet"
    )

    result = run_mlflow_experiment(snapshot_path)

    print("\nmlflow experiment selesai")
    print(f"tracking uri: {result['tracking_uri']}")
    print(f"experiment: {result['experiment_name']}")
    print(f"snapshot: {result['snapshot_name']}")
    print(f"dataset sha256: {result['dataset_sha256']}")
    print(
        f"baseline -> MAE {result['baseline_mae']:.3f}, "
        f"run {result['baseline_run_id']}"
    )
    print(
        f"model    -> MAE {result['model_mae']:.3f}, "
        f"run {result['model_run_id']}"
    )
    print(f"model uri: {result['model_uri']}")


if __name__ == "__main__":
    main()
