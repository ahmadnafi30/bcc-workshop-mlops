from time import perf_counter

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from mlflow.exceptions import MlflowException

from api.dependencies import (
    PERFORMANCE_SUMMARY_PATH,
    get_predictor,
)
from api.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictionRequest,
    PredictionResponse,
)
from monitoring.metrics import (
    API_REQUEST_LATENCY,
    API_REQUESTS,
    normalize_request_path,
    observe_prediction,
    render_metrics,
)
from serving.predictor import TaxiDemandPredictor

app = FastAPI(
    title="BCC Taxi Demand API",
    description="serve taxi demand forecast dari current MLflow champion model",
    version="0.1.0",
)


# catat request count dan latency tanpa bikin metric label dari arbitrary url
@app.middleware("http")
async def observe_http_request(
    request: Request,
    call_next,
):
    path = normalize_request_path(request.url.path)
    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        API_REQUEST_LATENCY.labels(
            method=request.method,
            path=path,
        ).observe(perf_counter() - started_at)

        API_REQUESTS.labels(
            method=request.method,
            path=path,
            status=str(status_code),
        ).inc()


# health endpoint cuma ngecek process API hidup dan bisa menerima request
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


# expose metric prometheus dan refresh model performance dari summary terbaru
@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    payload, content_type = render_metrics(PERFORMANCE_SUMMARY_PATH)

    return Response(
        content=payload,
        media_type=content_type,
    )


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
        observe_prediction(result)

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
