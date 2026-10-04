import os
from functools import lru_cache
from pathlib import Path

from serving.model_loader import RegistryModelLoader
from serving.predictor import TaxiDemandPredictor

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# bikin satu predictor instance yang bisa dipakai ulang antar request
@lru_cache
def get_predictor() -> TaxiDemandPredictor:
    # alias bisa dioverride dari environment tanpa ubah source code API
    alias = os.getenv("MODEL_ALIAS", "champion")
    demand_dir = PROJECT_ROOT / "data" / "processed" / "demand"

    return TaxiDemandPredictor(
        demand_dir=demand_dir,
        model_loader=RegistryModelLoader(alias=alias),
    )
