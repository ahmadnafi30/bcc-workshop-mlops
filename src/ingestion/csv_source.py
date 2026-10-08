"""The ingestion boundary: downloaded TLC Parquet becomes CSV before processing."""

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from data_versioning.pipeline_files import (
    file_fingerprint,
    write_csv_chunks_atomic,
    write_json_atomic,
)


def convert_parquet_to_csv(
    source_path: Path,
    output_path: Path | None = None,
    force: bool = False,
    batch_size: int = 100_000,
) -> dict[str, str | int]:
    """Convert all columns in bounded batches; also supports one-time legacy migration."""
    source_path = Path(source_path)
    output_path = Path(output_path) if output_path else source_path.with_suffix(".csv")
    if source_path.suffix != ".parquet" or output_path.suffix != ".csv":
        raise ValueError("conversion requires a .parquet source and a .csv destination")
    if batch_size < 1:
        raise ValueError("batch_size harus positif")
    manifest_path = output_path.with_suffix(".conversion.json")
    source_hash = file_fingerprint(source_path)
    if not force and output_path.exists() and manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (
                manifest["source_sha256"] == source_hash
                and manifest["csv_format"] == 1
                and manifest["output_sha256"] == file_fingerprint(output_path)
            ):
                return {
                    "path": str(output_path),
                    "rows": manifest["rows"],
                    "status": "cached",
                }
        except (OSError, ValueError, KeyError, TypeError):
            pass

    parquet = pq.ParquetFile(source_path)

    def frames():
        yielded = False
        for batch in parquet.iter_batches(batch_size=batch_size, use_threads=False):
            yielded = True
            yield batch.to_pandas()
        if not yielded:
            yield pd.DataFrame(columns=parquet.schema_arrow.names)

    try:
        rows = write_csv_chunks_atomic(frames(), output_path)
    finally:
        parquet.close()
    write_json_atomic(
        {
            "csv_format": 1,
            "source_sha256": source_hash,
            "output_sha256": file_fingerprint(output_path),
            "rows": rows,
        },
        manifest_path,
    )
    return {"path": str(output_path), "rows": rows, "status": "converted"}
