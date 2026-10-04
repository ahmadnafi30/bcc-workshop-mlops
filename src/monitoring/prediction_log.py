import json
from datetime import datetime, timezone
from pathlib import Path


class PredictionLogger:
    # siapin append-only jsonl log buat prediction yang nanti dipasangkan sama ground truth
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    # tulis satu prediction lengkap dengan model version dan waktu request
    def log(self, result: dict) -> None:
        # jsonl bikin setiap request satu line jadi gampang append dan dibaca ulang
        payload = {
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "zone_id": int(result["zone_id"]),
            "target_datetime": result["target_datetime"].isoformat(),
            "predicted_trip_count": float(result["predicted_trip_count"]),
            "model_name": str(result["model_name"]),
            "model_version": str(result["model_version"]),
            "model_alias": str(result["model_alias"]),
            "run_id": str(result["run_id"]),
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload) + "\n")


# load prediction jsonl dan skip line kosong kalau file pernah diedit manual
def load_prediction_log(path: Path) -> list[dict]:
    # file belum ada berarti memang belum ada prediction yang bisa dievaluate
    path = Path(path)

    if not path.exists():
        return []

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records
