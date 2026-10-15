"""Application configuration via environment variables."""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/forecast_db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
    # ML
    ARTIFACTS_DIR: str = "ml/artifacts"
    DATA_DIR: str = "data"
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
