import argparse
from pathlib import Path

from data_versioning.pipeline_files import read_csv_dataset, write_csv_atomic
from data_versioning.snapshot import (
    build_snapshot_name,
    create_training_snapshot,
    describe_snapshot,
)


# ambil cutoff date yang menentukan data mana yang boleh masuk training snapshot
def parse_args() -> argparse.Namespace:
    # default cutoff sama dengan akhir validation awal sebelum production replay mulai
    parser = argparse.ArgumentParser(
        description="buat versioned training snapshot dari feature dataset"
    )
    parser.add_argument(
        "--feature-path",
        type=Path,
        default=Path("data/features/taxi_demand_features.csv"),
        help="input features; DVC mengisi path training terpisah",
    )
    parser.add_argument(
        "--cutoff-date",
        default="2025-01-26",
        help="tanggal terakhir yang boleh masuk snapshot, format YYYY-MM-DD",
    )

    return parser.parse_args()


# bikin snapshot file yang nanti di-track sebagai output pipeline DVC
def main() -> None:
    # input dan output selalu dicari relatif dari root repository
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    feature_path = root / args.feature_path
    snapshot_dir = root / "data" / "snapshots" / "training"

    if not feature_path.exists():
        raise FileNotFoundError(
            f"feature dataset belum ada: {feature_path}. jalanin scripts/build_features.py dulu."
        )

    # filter feature dataset sesuai cutoff date lalu simpan sebagai immutable training input
    features = read_csv_dataset(feature_path)
    snapshot = create_training_snapshot(
        features=features,
        cutoff_date=args.cutoff_date,
    )

    output_path = snapshot_dir / build_snapshot_name(args.cutoff_date)
    write_csv_atomic(snapshot, output_path)

    # print fingerprint biar dataset version yang dipakai langsung kelihatan
    info = describe_snapshot(output_path)

    print("\ntraining snapshot siap")
    print(f"file: {info['name']}")
    print(f"rows: {info['rows']:,}")
    print(f"zones: {info['zones']}")
    print(f"sha256: {info['sha256']}")
    print(output_path)


if __name__ == "__main__":
    main()
