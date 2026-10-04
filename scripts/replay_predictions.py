import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from monitoring.prediction_log import PredictionLogger
from serving.model_loader import RegistryModelLoader
from serving.predictor import TaxiDemandPredictor


# ambil tanggal historical yang mau direplay sebagai online prediction
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="replay hourly prediction buat satu historical day"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="tanggal prediction replay, format YYYY-MM-DD",
    )

    return parser.parse_args()


# ambil semua Manhattan zone dari metadata TLC yang sudah dibootstrap
def load_manhattan_zone_ids(zone_lookup_path: Path) -> list[int]:
    zones = pd.read_csv(zone_lookup_path)

    return (
        zones.loc[
            zones["Borough"].astype(str).str.casefold().eq("manhattan"),
            "LocationID",
        ]
        .astype(int)
        .sort_values()
        .tolist()
    )


# replay prediction satu hari dengan rule feature yang sama seperti request FastAPI
def main() -> None:
    args = parse_args()
    target_date = date.fromisoformat(args.date)
    root = Path(__file__).resolve().parents[1]

    demand_dir = root / "data" / "processed" / "demand"
    zone_lookup_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"
    prediction_path = root / "data" / "monitoring" / "predictions.jsonl"

    if not zone_lookup_path.exists():
        raise FileNotFoundError(
            "taxi zone lookup belum ada, jalanin bootstrap_data.py dulu"
        )

    predictor = TaxiDemandPredictor(
        demand_dir=demand_dir,
        model_loader=RegistryModelLoader(alias="champion"),
        prediction_logger=PredictionLogger(prediction_path),
    )
    zone_ids = load_manhattan_zone_ids(zone_lookup_path)

    total = 0

    # historical replay dipercepat, tapi setiap prediction tetap cuma baca history sebelum target hour
    for hour in range(24):
        target_datetime = datetime.combine(
            target_date,
            datetime.min.time(),
        ).replace(hour=hour)

        for zone_id in zone_ids:
            predictor.predict(
                zone_id=zone_id,
                target_datetime=target_datetime,
            )
            total += 1

    print(
        f"{target_date.isoformat()} -> "
        f"{total:,} predictions dari {len(zone_ids)} zones"
    )
    print(prediction_path)


if __name__ == "__main__":
    main()
