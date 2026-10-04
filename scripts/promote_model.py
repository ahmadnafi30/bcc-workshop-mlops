import argparse

from tracking.mlflow_tracking import configure_mlflow
from tracking.model_registry import promote_model_version


# ambil model version yang sudah direview dan siap dipromote
def parse_args() -> argparse.Namespace:
    # champion jadi default karena alias ini nanti yang dipakai service production
    parser = argparse.ArgumentParser(
        description="promote registered model version ke production alias"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="model version yang mau dipromote",
    )
    parser.add_argument(
        "--alias",
        default="champion",
        help="alias tujuan, default champion",
    )

    return parser.parse_args()


# pindahin alias production ke model version yang sudah dipilih
def main() -> None:
    # configure client ke MLflow server yang sama dengan registry
    args = parse_args()
    configure_mlflow()

    result = promote_model_version(
        version=args.version,
        alias=args.alias,
    )

    print("\nmodel promoted")
    print(f"name: {result['model_name']}")
    print(f"version: {result['version']}")
    print(f"alias: {result['alias']}")
    print(f"uri: {result['model_uri']}")


if __name__ == "__main__":
    main()
