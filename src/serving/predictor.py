from datetime import datetime
from pathlib import Path

from serving.feature_provider import build_online_features
from serving.model_loader import RegistryModelLoader


class TaxiDemandPredictor:
    # siapin predictor dengan lokasi processed demand dan model registry loader
    def __init__(
        self,
        demand_dir: Path,
        model_loader: RegistryModelLoader | None = None,
    ) -> None:
        self.demand_dir = Path(demand_dir)
        self.model_loader = model_loader or RegistryModelLoader()

    # kasih info model yang sekarang dipakai tanpa perlu jalanin prediction
    def get_model_info(self) -> dict[str, str]:
        return self.model_loader.get_model_info()

    # bikin online features lalu predict demand satu zone untuk target hour
    def predict(
        self,
        zone_id: int,
        target_datetime: datetime,
    ) -> dict[str, str | int | float | datetime]:
        # feature provider cuma baca historical demand yang strictly sebelum target time
        features = build_online_features(
            demand_dir=self.demand_dir,
            zone_id=zone_id,
            target_datetime=target_datetime,
        )

        # loader otomatis refresh kalau alias champion pindah ke model version baru
        model, model_info = self.model_loader.get_model()
        prediction = float(model.predict(features)[0])

        # demand nggak mungkin negatif, jadi output model dibatasi minimum nol
        predicted_trip_count = max(0.0, prediction)

        return {
            "zone_id": zone_id,
            "target_datetime": target_datetime,
            "predicted_trip_count": predicted_trip_count,
            **model_info,
        }
