"""Prediction endpoints."""
from fastapi import APIRouter, Request, HTTPException
from backend.schemas import (PredictionRequest, PredictionResponse,
                             BatchPredictionRequest, BatchPredictionResponse)
import pandas as pd

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, req: Request):
    """Generate demand forecast for a single SKU-store combination."""
    model_mgr = req.app.state.model_manager
    
    dates = pd.date_range(request.start_date, request.end_date, freq="D")
    date_strings = [d.strftime("%Y-%m-%d") for d in dates]
    
    if len(date_strings) > 90:
        raise HTTPException(400, "Date range cannot exceed 90 days")
    
    forecasts = model_mgr.predict(request.sku, request.store_id, date_strings)
    
    return PredictionResponse(
        sku=request.sku, store_id=request.store_id,
        forecasts=forecasts, model_used="hybrid"
    )


@router.post("/batch_predict", response_model=BatchPredictionResponse)
async def batch_predict(request: BatchPredictionRequest, req: Request):
    """Generate forecasts for multiple SKU-store combinations."""
    model_mgr = req.app.state.model_manager
    
    if len(request.predictions) > 100:
        raise HTTPException(400, "Batch size cannot exceed 100")
    
    results = []
    total = 0
    for pred_req in request.predictions:
        dates = pd.date_range(pred_req.start_date, pred_req.end_date, freq="D")
        date_strings = [d.strftime("%Y-%m-%d") for d in dates]
        forecasts = model_mgr.predict(pred_req.sku, pred_req.store_id, date_strings)
        results.append(PredictionResponse(
            sku=pred_req.sku, store_id=pred_req.store_id,
            forecasts=forecasts, model_used="hybrid"
        ))
        total += len(forecasts)
    
    return BatchPredictionResponse(results=results, total_forecasts=total)
