"""Core configuration management for MemoryMeet."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "MemoryMeet - AI Meeting Prep Agent"
    VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["*"]
    
    # Local Storage
    UPLOAD_DIR: str = "./uploads"
    
    # Database
    DATABASE_URL: str = "sqlite:///./memorymeet.db"
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"
    OPENAI_API_KEY: str = ""
    
    # Hindsight Long-Term Memory Service
    HINDSIGHT_API_KEY: str = ""
    HINDSIGHT_ENDPOINT: str = "https://api.hindsight.vectorize.io"
    HINDSIGHT_BANK_ID: str = "memorymeet_agent"
    
    # Speech-to-Text Configuration
    STT_PROVIDER: str = "gemini_multimodal"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
