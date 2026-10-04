from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    model_alias: str
    run_id: str
    model_uri: str


class PredictionRequest(BaseModel):
    zone_id: int = Field(gt=0)
    target_datetime: datetime

    # validasi target time dari request sebelum masuk ke serving layer
    @field_validator("target_datetime")
    @classmethod
    def validate_target_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            raise ValueError(
                "target_datetime harus tanpa timezone dan dianggap sebagai waktu lokal NYC"
            )

        if (
            value.minute != 0
            or value.second != 0
            or value.microsecond != 0
        ):
            raise ValueError(
                "target_datetime harus pas di awal jam, "
                "contoh 2025-01-28T18:00:00"
            )

        return value


class PredictionResponse(BaseModel):
    zone_id: int
    target_datetime: datetime
    predicted_trip_count: float
    model_name: str
    model_version: str
    model_alias: str
    run_id: str
    model_uri: str
