"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for development. Production deployments should set all required variables.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings are automatically loaded from:
    1. Environment variables
    2. .env file (if present)

    All settings use UPPERCASE names in .env but lowercase in code.
    """

    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    database_url: str = "postgresql+asyncpg://valueinvest:valueinvest_dev_password@localhost:5432/valueinvestai"
    redis_url: str = "redis://localhost:6379/0"

    # PostgreSQL credentials (for docker-compose)
    postgres_user: str = "valueinvest"
    postgres_password: str = "valueinvest_dev_password"
    postgres_db: str = "valueinvestai"

    # ==========================================================================
    # External API Keys
    # ==========================================================================
    eod_api_key: str = ""
    fmp_api_key: str = ""
    gemini_api_key: str = ""

    # ==========================================================================
    # Application Settings
    # ==========================================================================
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"

    # ==========================================================================
    # API Settings
    # ==========================================================================
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ==========================================================================
    # Rate Limiting & Caching
    # ==========================================================================
    rate_limit_per_minute: int = 60
    cache_ttl_financials: int = 3600  # 1 hour
    cache_ttl_prices: int = 300  # 5 minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def database_url_sync(self) -> str:
        """
        Get synchronous database URL (for Alembic migrations).

        Converts asyncpg URL to psycopg2 format.
        """
        return self.database_url.replace("+asyncpg", "")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are only loaded once and reused.
    Call get_settings.cache_clear() if you need to reload settings.
    """
    return Settings()
