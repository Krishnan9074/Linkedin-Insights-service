import os
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, validator, Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "LinkedIn Insights Microservice"
    API_V1_STR: str = "/api"
    
    # MongoDB settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "linkedin_insights"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    CACHE_TTL: int = 300  # 5 minutes
    
    # LinkedIn scraper settings
    LINKEDIN_EMAIL: Optional[str] = None
    LINKEDIN_PASSWORD: Optional[str] = None
    LINKEDIN_BASE_URL: str = "https://www.linkedin.com"
    MAX_POSTS_TO_SCRAPE: int = 15
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Gemini AI settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"  # Using the Gemini Pro model
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()

# Initialize empty __init__.py files
init_files = [
    "app/core/__init__.py",
    "app/api/__init__.py",
    "app/db/__init__.py",
    "app/models/__init__.py",
    "app/schemas/__init__.py",
    "app/scraper/__init__.py",
    "app/services/__init__.py",
] 