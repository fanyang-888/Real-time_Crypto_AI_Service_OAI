"""
FastAPI route handlers
"""
import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from .metrics import (
    prediction_requests_total,
    prediction_errors_total,
    http_request_duration_seconds
)
from .model_loader import ModelLoader

router = APIRouter()


class PredictionRow(BaseModel):
    """Single row for prediction input"""
    ret_mean: float = Field(..., description="Mean return")
    ret_std: float = Field(..., description="Standard deviation of returns")
    n: int = Field(..., gt=0, description="Number of observations")
    
    @field_validator('ret_mean', 'ret_std')
    @classmethod
    def validate_numeric(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError("Must be a number")
        return float(v)


class PredictionRequest(BaseModel):
    """Batch prediction request"""
    rows: List[PredictionRow] = Field(..., min_length=1, description="List of feature rows")
    
    @field_validator('rows')
    @classmethod
    def validate_rows(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one row is required")
        if len(v) > 1000:
            raise ValueError("Maximum 1000 rows per request")
        return v


class PredictionResponse(BaseModel):
    """Prediction response"""
    scores: List[float] = Field(..., description="Prediction scores")
    model_variant: str = Field(..., description="Model variant used")
    version: str = Field(..., description="Model version")
    ts: str = Field(..., description="UTC timestamp")


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: Request, pred_request: PredictionRequest):
    """
    Batch prediction endpoint
    
    Accepts a batch of feature rows and returns predictions
    """
    start_time = time.time()
    
    try:
        model_loader: ModelLoader = request.app.state.model_loader
        
        if model_loader is None or not model_loader.is_loaded():
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. Service unavailable."
            )
        
        # Extract features
        features = []
        for row in pred_request.rows:
            features.append([row.ret_mean, row.ret_std, row.n])
        
        # Get predictions
        predictions = model_loader.predict(features)
        
        # Record metrics
        prediction_requests_total.labels(
            model_variant=model_loader.get_variant(),
            status="success"
        ).inc()
        
        latency = time.time() - start_time
        http_request_duration_seconds.labels(
            method="POST",
            endpoint="/predict",
            status_code=200
        ).observe(latency)
        
        return PredictionResponse(
            scores=predictions.tolist() if hasattr(predictions, 'tolist') else list(predictions),
            model_variant=model_loader.get_variant(),
            version=model_loader.get_version(),
            ts=datetime.now(timezone.utc).isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        # Record error metrics
        model_loader: ModelLoader = request.app.state.model_loader
        variant = model_loader.get_variant() if model_loader and model_loader.is_loaded() else "unknown"
        prediction_errors_total.labels(
            model_variant=variant,
            error_type=type(e).__name__
        ).inc()
        
        latency = time.time() - start_time
        http_request_duration_seconds.labels(
            method="POST",
            endpoint="/predict",
            status_code=500
        ).observe(latency)
        
        raise HTTPException(
            status_code=400,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/health")
async def health(request: Request):
    """
    Health check endpoint
    
    Returns service health status
    """
    model_loader: ModelLoader = request.app.state.model_loader
    
    if model_loader is None or not model_loader.is_loaded():
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": "Model not loaded"}
        )
    
    return {"status": "ok"}


@router.get("/version")
async def version(request: Request):
    """
    Version endpoint
    
    Returns current model version and git SHA
    """
    model_loader: ModelLoader = request.app.state.model_loader
    
    if model_loader is None:
        return {
            "model": "unknown",
            "sha": os.getenv("GIT_SHA", "unknown")
        }
    
    return {
        "model": model_loader.get_version(),
        "sha": os.getenv("GIT_SHA", "unknown")
    }

