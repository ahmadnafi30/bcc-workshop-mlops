from fastapi import Depends, FastAPI, HTTPException
from mlflow.exceptions import MlflowException

from api.dependencies import get_predictor
from api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
)
from serving.predictor import TaxiDemandPredictor

app = FastAPI(
    title="BCC Taxi Demand API",
    description="serve taxi demand forecast dari current MLflow champion model",
    version="0.1.0",
)


# health endpoint cuma ngecek process API hidup dan bisa menerima request
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


# tampilkan model version yang sekarang ditunjuk alias serving
@app.get("/model-info", response_model=ModelInfoResponse)
def model_info(
    predictor: TaxiDemandPredictor = Depends(get_predictor),
) -> ModelInfoResponse:
    try:
        return ModelInfoResponse(**predictor.get_model_info())
    except MlflowException as error:
        raise HTTPException(
            status_code=503,
            detail="model champion belum tersedia di MLflow Registry",
        ) from error


# predict demand satu zone untuk satu target hour
@app.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    predictor: TaxiDemandPredictor = Depends(get_predictor),
) -> PredictionResponse:
    try:
        result = predictor.predict(
            zone_id=request.zone_id,
            target_datetime=request.target_datetime,
        )
        return PredictionResponse(**result)
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    except MlflowException as error:
        raise HTTPException(
            status_code=503,
            detail="model champion belum tersedia di MLflow Registry",
        ) from error
