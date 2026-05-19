"""
DATASHIELD Configuration Module
Centralized settings with environment variable validation.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = "DATASHIELD"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "1.0.0"
    APP_SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for signing tokens and cookies",
    )

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://datashield:securepassword@localhost:5432/datashield"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # --- JWT ---
    JWT_SECRET_KEY: str = "dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- AI/ML ---
    AI_CLASSIFICATION_THRESHOLD: float = 0.75
    AI_ANOMALY_THRESHOLD: float = 0.80
    AI_MODEL_PATH: str = "./models"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Rate Limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def sync_database_url(self) -> str:
        """Convert async URL to sync for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
