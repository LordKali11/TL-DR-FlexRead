import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "NZZ FlexRead API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend for NZZ FlexRead - Stream 2: Data & Content Personalisation (English Edition)"
    
    # Environment & GCP Cloud Run Port
    ENV: str = os.environ.get("ENV", "development")
    DEBUG: bool = os.environ.get("DEBUG", "true").lower() == "true"
    PORT: int = int(os.environ.get("PORT", "8080"))
    
    # Base paths
    WORKSPACE_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    INPUT_DIR: Path = WORKSPACE_ROOT / "input"
    DATA_DIR: Path = WORKSPACE_ROOT / "backend" / "data"
    
    # Google Cloud Platform & Gemini / Vertex AI Settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
    GOOGLE_CLOUD_LOCATION: str = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")
    USE_VERTEX_AI: bool = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true"
    GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Language focus
    DEFAULT_LANGUAGE: str = "en"
    
    # Multi-tier Cache settings (sqlite | redis | firestore | memory)
    CACHE_TYPE: str = os.environ.get("CACHE_TYPE", "sqlite")
    REDIS_URL: Optional[str] = os.environ.get("REDIS_URL")
    CACHE_TTL_SECONDS: int = 86400 * 7  # 7 days
    
    # Reading speed parameter
    DEFAULT_WPM: int = 220  # Average adult reading speed in words per minute
    
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()

# Ensure data directory exists
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
