"""Health check endpoint."""
from fastapi import APIRouter
from backend.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    from fastapi import Request
    return HealthResponse(status="healthy", models_loaded=True, version="1.0.0")
