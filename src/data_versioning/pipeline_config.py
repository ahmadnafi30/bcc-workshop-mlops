import json
from datetime import date
from pathlib import Path

from data_versioning.snapshot import build_snapshot_name


def load_training_dates(project_root: Path) -> dict[str, str]:
    config = json.loads((Path(project_root) / "params.json").read_text(encoding="utf-8"))
    start = date.fromisoformat(config["data"]["history_start"])
    cutoff = date.fromisoformat(config["data"]["training_cutoff"])
    if cutoff < start:
        raise ValueError("training_cutoff harus sama atau setelah history_start")
    return {"history_start": start.isoformat(), "training_cutoff": cutoff.isoformat()}


def training_snapshot_path(project_root: Path) -> Path:
    dates = load_training_dates(project_root)
    return (
        Path(project_root)
        / "data/snapshots/training"
        / build_snapshot_name(dates["training_cutoff"])
    )
