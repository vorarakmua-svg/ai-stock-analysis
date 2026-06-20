"""
Application configuration using Pydantic Settings.

Loads environment variables from .env file and provides typed configuration
for the Intelligent Investor Pro backend application.
"""

import json
import warnings
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        APP_ENV: Application environment (development, staging, production)
        DEBUG: Enable debug mode with verbose logging
        API_PREFIX: API route prefix for versioning
        DATA_DIR: Root directory for data files
        CSV_PATH: Path to summary.csv file
        JSON_DIR: Directory containing per-stock JSON files
        CORS_ORIGINS: List of allowed CORS origins
        GOOGLE_API_KEY: Google AI (Gemini) API key for AI features
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Settings
    APP_ENV: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(
        default=False, description="Enable debug mode (should be False in production)"
    )
    API_PREFIX: str = Field(default="/api/v1", description="API route prefix")

    # Data Paths - relative to project root (parent of backend directory)
    DATA_DIR: str = Field(default="../data", description="Root directory for data files")
    CSV_PATH: str = Field(
        default="../data/output/csv/summary.csv", description="Path to summary CSV file"
    )
    JSON_DIR: str = Field(
        default="../data/output/json", description="Directory containing stock JSON files"
    )

    # CORS Settings - include common Next.js dev ports
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
        ],
        description="Allowed CORS origins",
    )

    # AI Integration
    GOOGLE_API_KEY: str = Field(default="", description="Google AI (Gemini) API key")
    GEMINI_MODEL_NAME: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model name for AI analysis (e.g., gemini-2.5-flash, gemini-1.5-pro)",
    )
    LLM_PROVIDER: str = Field(
        default="gemini", description="LLM provider backend (currently only 'gemini')"
    )
    # gemini-2.5-flash is a 'thinking' model; reasoning tokens count against the
    # output budget. 0 disables thinking, -1 lets the model decide, None uses the
    # SDK default. Deterministic JSON extraction does not need thinking; the
    # narrative analyst benefits from it.
    GEMINI_EXTRACTION_THINKING_BUDGET: int = Field(
        default=0, description="Thinking-token budget for extraction calls (0 disables thinking)"
    )
    GEMINI_ANALYST_THINKING_BUDGET: int = Field(
        default=-1, description="Thinking-token budget for analyst calls (-1 = model decides)"
    )

    # Observability
    LOG_LEVEL: str = Field(
        default="INFO", description="Root log level (DEBUG, INFO, WARNING, ERROR)"
    )
    LOG_JSON: bool = Field(
        default=True,
        description="Emit structured JSON logs (set False for human-readable dev logs)",
    )
    ENABLE_METRICS: bool = Field(default=True, description="Expose Prometheus metrics at /metrics")
    SENTRY_DSN: str = Field(
        default="", description="Sentry DSN for error tracking (disabled when empty)"
    )

    # Persistence (optional; empty disables and the app stays file/disk-only)
    DATABASE_URL: str = Field(
        default="", description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host/db"
    )
    REDIS_URL: str = Field(
        default="", description="Redis URL, e.g. redis://localhost:6379/0 (empty disables)"
    )
    CACHE_BACKEND: str = Field(
        default="disk", description="Cache backend: 'disk' (diskcache) or 'redis'"
    )

    # Cache Settings
    CACHE_DIR: str = Field(default="./cache", description="Directory for diskcache storage")
    PRICE_CACHE_TTL: int = Field(default=30, description="Real-time price cache TTL in seconds")
    EXTRACTION_CACHE_TTL: int = Field(
        default=604800, description="AI extraction cache TTL in seconds (7 days)"
    )
    VALUATION_CACHE_TTL: int = Field(
        default=86400, description="Valuation cache TTL in seconds (24 hours)"
    )
    ANALYSIS_CACHE_TTL: int = Field(
        default=604800, description="AI analysis cache TTL in seconds (7 days)"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            # Handle JSON-like string format: ["http://localhost:3000"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(origin) for origin in parsed]
                except json.JSONDecodeError:
                    pass
            # Handle comma-separated format
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("GOOGLE_API_KEY", mode="after")
    @classmethod
    def validate_google_api_key(cls, v: str) -> str:
        """Warn if Google API key is not set (required for AI features)."""
        if not v:
            warnings.warn(
                "GOOGLE_API_KEY is not set. AI features (valuation, analysis) will not work.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @property
    def project_root(self) -> Path:
        """Get the project root directory (parent of backend)."""
        return Path(__file__).parent.parent.parent

    @property
    def csv_path_resolved(self) -> Path:
        """Get the resolved absolute path to summary.csv."""
        backend_dir = Path(__file__).parent.parent
        return (backend_dir / self.CSV_PATH).resolve()

    @property
    def json_dir_resolved(self) -> Path:
        """Get the resolved absolute path to JSON directory."""
        backend_dir = Path(__file__).parent.parent
        return (backend_dir / self.JSON_DIR).resolve()

    @property
    def data_dir_resolved(self) -> Path:
        """Get the resolved absolute path to data directory."""
        backend_dir = Path(__file__).parent.parent
        return (backend_dir / self.DATA_DIR).resolve()

    @property
    def cache_dir_resolved(self) -> Path:
        """Get the resolved absolute path to cache directory."""
        backend_dir = Path(__file__).parent.parent
        return (backend_dir / self.CACHE_DIR).resolve()


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings instance.

    Returns:
        Settings: Application settings singleton.

    Note:
        Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
