"""
Configuration settings for SoundForge AI
"""

from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    APP_ENV: str = "production"
    
    # Storage settings
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    STORAGE_DIR: str = "./storage"
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "soundforge-audio"
    S3_REGION: str = "us-east-1"
    
    # Audio settings
    DEFAULT_SAMPLE_RATE: int = 48000
    DEFAULT_TARGET_LOUDNESS: float = -14.0
    MAX_TRUE_PEAK_DBTP: float = -1.0
    MAX_DURATION_SECONDS: float = 600.0
    MIN_DURATION_SECONDS: float = 1.0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
