import argparse
from datetime import date, datetime
import os
from pathlib import Path

import pandas as pd
import requests


# ambil tanggal dan jam yang mau dikirim ke prediction API
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="kirim prediction requests ke FastAPI buat demo metrics + logging"
    )
    parser.add_argument(
        "--date",
        required=True,
        help="tanggal target, format YYYY-MM-DD",
    )
    parser.add_argument(
        "--start-hour",
        type=int,
        default=17,
        choices=range(24),
        metavar="[0-23]",
    )
    parser.add_argument(
        "--end-hour",
        type=int,
        default=18,
        choices=range(24),
        metavar="[0-23]",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "http://127.0.0.1:8000"),
    )

    return parser.parse_args()


# load semua Manhattan taxi zone id dari metadata yang sudah dibootstrap
def load_zone_ids(zone_lookup_path: Path) -> list[int]:
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


# kirim request lewat HTTP supaya operational metrics dan prediction log sama-sama terisi
def main() -> None:
    args = parse_args()

    if args.end_hour < args.start_hour:
        raise ValueError("end-hour harus sama atau setelah start-hour")

    target_date = date.fromisoformat(args.date)
    root = Path(__file__).resolve().parents[1]
    lookup_path = root / "data" / "metadata" / "taxi_zone_lookup.csv"

    if not lookup_path.exists():
        raise FileNotFoundError(
            "taxi zone lookup belum ada. jalanin bootstrap_data.py dulu."
        )

    zone_ids = load_zone_ids(lookup_path)
    success = 0
    failed = 0

    for hour in range(args.start_hour, args.end_hour + 1):
        target_datetime = datetime.combine(
            target_date,
            datetime.min.time(),
        ).replace(hour=hour)

        for zone_id in zone_ids:
            response = requests.post(
                f"{args.api_url.rstrip('/')}/predict",
                json={
                    "zone_id": zone_id,
                    "target_datetime": target_datetime.isoformat(),
                },
                timeout=30,
            )

            if response.ok:
                success += 1
            else:
                failed += 1
                print(
                    f"failed zone={zone_id} hour={hour}: "
                    f"{response.status_code} {response.text}"
                )

    print()
    print(f"api traffic selesai -> {success} success, {failed} failed")
    print(f"target api: {args.api_url}")


if __name__ == "__main__":
    main()
