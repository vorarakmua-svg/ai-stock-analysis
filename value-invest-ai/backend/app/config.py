from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/valueinvestai"
    redis_url: str = "redis://localhost:6379/0"

    # External APIs
    eod_api_key: str = ""
    fmp_api_key: str = ""
    gemini_api_key: str = ""

    # Application
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # API Settings
    api_v1_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
