"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class PredictionRequest(BaseModel):
    sku: str = Field(..., example="dairy_whole_milk")
    store_id: str = Field(..., example="store_001")
    start_date: date = Field(..., example="2025-04-01")
    end_date: date = Field(..., example="2025-04-07")
    
class PredictionResponse(BaseModel):
    sku: str
    store_id: str
    forecasts: List[dict]
    model_used: str = "hybrid"

class BatchPredictionRequest(BaseModel):
    predictions: List[PredictionRequest]

class BatchPredictionResponse(BaseModel):
    results: List[PredictionResponse]
    total_forecasts: int

class MetricsResponse(BaseModel):
    model: str
    mae: float
    rmse: float
    mape: float
    smape: Optional[float] = None
    r2: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    version: str

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DataUploadResponse(BaseModel):
    message: str
    records_processed: int
    filename: str
