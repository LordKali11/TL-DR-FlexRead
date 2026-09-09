import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory hierarchy
CURRENT_DIR = Path(__file__).resolve().parent      # backend/app
BACKEND_DIR = CURRENT_DIR.parent                   # backend
WORKSPACE_ROOT = BACKEND_DIR.parent                # TL-DR-FlexRead

# Proactively locate and load .env files into environment
env_candidates = [
    BACKEND_DIR / ".env",
    WORKSPACE_ROOT / ".env",
    Path(".env").resolve(),
    Path("backend/.env").resolve(),
]
loaded_env_path = None
for env_path in env_candidates:
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path, override=False)
        if not loaded_env_path:
            loaded_env_path = str(env_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "NZZ FlexRead API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend for NZZ FlexRead - Stream 2: Data & Content Personalisation (MongoDB & Redis Architecture)"
    
    # Environment & GCP Cloud Run Port
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8080
    
    # Base paths
    WORKSPACE_ROOT: Path = WORKSPACE_ROOT
    INPUT_DIR: Path = WORKSPACE_ROOT / "input"
    DATA_DIR: Path = BACKEND_DIR / "data"
    
    # Primary Persistent Database: MongoDB Cloud / Remote Instance
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "nzz-flexread-db"
    MONGODB_TLS_ALLOW_INVALID_CERTS: bool = True
    MONGODB_SERVER_SELECTION_TIMEOUT_MS: int = 10000
    
    # Cache Layer Toggle & Redis Settings
    ENABLE_REDIS: bool = False  # Set to False to bypass Redis gracefully and use in-memory cache
    CACHE_TYPE: str = "memory"
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL_SECONDS: int = 86400 * 7  # 7 days
    
    # Google Cloud Platform & Gemini / Vertex AI Settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: str = "europe-west1"
    USE_VERTEX_AI: bool = False
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.6-flash"
    
    # Language focus
    DEFAULT_LANGUAGE: str = "en"
    
    # Reading speed parameter
    DEFAULT_WPM: int = 220  # Average adult reading speed in words per minute
    
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in env_candidates if p.is_file()] or ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_redis_url(self) -> str:
        """Resolves the effective Redis connection URL."""
        if self.REDIS_HOST:
            auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return self.REDIS_URL

settings = Settings()

# Ensure fallback data directory exists
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
