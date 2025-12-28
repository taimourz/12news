# app/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    API_KEY: str

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Dawn Archive API"
    VERSION: str = "3.0.0"
    
    BASE_URL: str = "https://www.dawn.com/newspaper"
    DATA_DIR: Path = Path("./data")
    DELAY: int = 3
    
    PROXY_URL: str | None = None
    
    HEADLESS: bool = True
    MAX_RETRIES: int = 2
    TIMEOUT: int = 90000
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore", 
    )

settings = Settings(API_KEY=os.environ.get("TAIMOUR_API_KEY"))
