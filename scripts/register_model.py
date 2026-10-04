import argparse

from tracking.mlflow_tracking import configure_mlflow
from tracking.model_registry import register_run_model


# ambil run id yang mau dijadikan registered model version
def parse_args() -> argparse.Namespace:
    # default alias challenger karena model baru belum otomatis dianggap production
    parser = argparse.ArgumentParser(
        description="register MLflow run sebagai candidate model"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="run id dari hist-gradient-boosting experiment",
    )
    parser.add_argument(
        "--alias",
        default="challenger",
        help="alias candidate yang mau dipasang",
    )

    return parser.parse_args()


# register trained model dari experiment run ke model registry
def main() -> None:
    # tracking uri harus sama dengan server tempat experiment run tadi disimpan
    args = parse_args()
    configure_mlflow()

    result = register_run_model(
        run_id=args.run_id,
        alias=args.alias,
    )

    print("\nmodel registered")
    print(f"name: {result['model_name']}")
    print(f"version: {result['version']}")
    print(f"alias: {result['alias']}")
    print(f"uri: {result['model_uri']}")


if __name__ == "__main__":
    main()
