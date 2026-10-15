"""
FastAPI Backend for Perishable Goods Forecasting System

Production-ready API with:
- JWT authentication
- Prediction endpoints (single + batch)
- Metrics and health endpoints
- Data upload
- Pydantic validation
- CORS support
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routes.predictions import router as predictions_router
from backend.routes.metrics import router as metrics_router
from backend.routes.auth import router as auth_router
from backend.routes.data import router as data_router
from backend.routes.health import router as health_router
from backend.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lazy-load models on startup."""
    logger.info("Starting up Forecast API...")
    from backend.model_loader import ModelManager
    app.state.model_manager = ModelManager()
    app.state.model_manager.load_models()
    logger.info("Models loaded successfully.")
    yield
    logger.info("Shutting down Forecast API...")


app = FastAPI(
    title="Perishable Goods Forecasting API",
    description="Large-scale demand forecasting for perishable retail goods using RF + LSTM hybrid models",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(predictions_router, prefix="/api", tags=["Predictions"])
app.include_router(metrics_router, prefix="/api", tags=["Metrics"])
app.include_router(data_router, prefix="/api", tags=["Data"])


@app.get("/")
async def root():
    return {"message": "Perishable Goods Forecasting API", "version": "1.0.0",
            "docs": "/docs"}
