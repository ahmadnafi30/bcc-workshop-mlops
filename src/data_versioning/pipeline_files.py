"""Small helpers for local workshop artifacts and file fingerprints."""

import json
import os
from collections.abc import Iterable, Iterator
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pandas as pd


def file_fingerprint(path: Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_csv_dates(frame: pd.DataFrame) -> pd.DataFrame:
    # CSV stores text: restore dates before feature engineering and time comparisons.
    for column in ("timestamp", "target_datetime", "tpep_pickup_datetime"):
        if column in frame.columns:
            errors = "coerce" if column == "tpep_pickup_datetime" else "raise"
            frame[column] = pd.to_datetime(frame[column], errors=errors, format="mixed")
    if "logged_at" in frame.columns:
        frame["logged_at"] = pd.to_datetime(frame["logged_at"], errors="raise", utc=True)
    return frame


def read_csv_dataset(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    """Read readable data with explicit datetime parsing and accurate float round trips."""
    frame = pd.read_csv(path, usecols=columns, float_precision="round_trip")
    return _parse_csv_dates(frame)


def iter_csv_chunks(
    path: Path, columns: list[str] | None = None, chunksize: int = 100_000
) -> Iterator[pd.DataFrame]:
    """Read a monthly CSV in bounded chunks rather than loading every trip at once."""
    with pd.read_csv(
        path, usecols=columns, chunksize=chunksize, float_precision="round_trip"
    ) as reader:
        for frame in reader:
            yield _parse_csv_dates(frame)


def write_csv_chunks_atomic(frames: Iterable[pd.DataFrame], output_path: Path) -> int:
    """Write chunks to one CSV and publish it only when the entire operation succeeds."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.{uuid4().hex}.tmp")
    rows = 0
    header = True
    try:
        with temporary.open("w", encoding="utf-8", newline="") as destination:
            for frame in frames:
                frame.to_csv(destination, index=False, header=header, lineterminator="\n")
                rows += len(frame)
                header = False
        if header:
            raise ValueError(
                "CSV writer needs at least one frame, including headers for empty data"
            )
        temporary.chmod(0o644)
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)
    return rows


def write_csv_atomic(frame: pd.DataFrame, output_path: Path) -> None:
    """Publish a complete CSV file, including a header for an empty result."""
    write_csv_chunks_atomic([frame], output_path)


def write_json_atomic(value: dict, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
        os.replace(temporary, output_path)
    finally:
        temporary.unlink(missing_ok=True)
