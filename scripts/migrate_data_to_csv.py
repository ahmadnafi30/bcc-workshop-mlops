"""One-time migration for workshop data created by the earlier Parquet pipeline."""

import argparse
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from data_versioning.pipeline_files import write_json_atomic
from ingestion.csv_source import convert_parquet_to_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert existing workshop data to readable CSV")
    parser.add_argument(
        "--dry-run", action="store_true", help="show paths without writing/moving data"
    )
    parser.add_argument(
        "--keep-legacy", action="store_true", help="leave old derived Parquet in place"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    downloaded = sorted((root / "data/source/tlc").glob("*.parquet"))
    generated = []
    for directory in (
        "data/source/replay",
        "data/raw/trips",
        "data/processed/demand",
        "data/features",
        "data/snapshots/training",
        "data/monitoring",
    ):
        generated.extend(sorted((root / directory).rglob("*.parquet")))
    session = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid4().hex[:6]
    archive_root = root / "data/legacy_parquet" / session
    report = []

    for source in [*downloaded, *generated]:
        # Resolve every individual move/conversion within the explicitly named project.
        source = source.resolve()
        relative = source.relative_to(root)
        destination = source.with_suffix(".csv")
        destination.resolve().relative_to(root)
        original_download = source in downloaded
        print(f"{relative} -> {destination.relative_to(root)}", flush=True)
        if args.dry_run:
            continue
        if destination.exists() and not original_download:
            info = {"path": str(destination), "status": "existing_csv_kept"}
        else:
            info = convert_parquet_to_csv(source, destination)
        entry = {"source": str(relative), **info}
        if not original_download and not args.keep_legacy:
            archived = archive_root / relative
            archived.resolve().relative_to(root)
            archived.parent.mkdir(parents=True, exist_ok=True)
            source.replace(archived)
            entry["archived_to"] = str(archived.relative_to(root))
            conversion_manifest = destination.with_suffix(".conversion.json")
            if conversion_manifest.exists():
                conversion_manifest.replace(archived.with_suffix(".conversion.json"))
        report.append(entry)
        print(f"  {info['status']}", flush=True)

    if not args.dry_run:
        report_path = root / "data/experiments/csv-migration" / f"{session}.json"
        write_json_atomic({"files": report, "archive_root": str(archive_root)}, report_path)
        print(f"Migration report: {report_path}")
    print("Parquet downloads are retained; active data processing now uses CSV.")


if __name__ == "__main__":
    main()
