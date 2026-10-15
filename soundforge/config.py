"""
Configuration settings for SoundForge AI (PS1 Specification)
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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
    
    # Audio settings (PS1 Specification)
    DEFAULT_SAMPLE_RATE: int = 48000
    DEFAULT_TARGET_LOUDNESS: float = -16.0
    MAX_TRUE_PEAK_DBTP: float = -1.0
    MIN_DURATION_SECONDS: float = 5.0
    MAX_DURATION_SECONDS: float = 300.0
    DURATION_TOLERANCE_SECONDS: float = 0.05
    LOUDNESS_TOLERANCE_LU: float = 1.0
    
    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()
