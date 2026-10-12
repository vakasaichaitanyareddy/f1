from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "APEX GP API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./apex_gp.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-32-chars-long-minimum-replace-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Provider Settings
    OPENF1_BASE_URL: str = "https://api.openf1.org/v1"
    JOLPICA_BASE_URL: str = "https://api.jolpi.ca/ergast/f1"

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
