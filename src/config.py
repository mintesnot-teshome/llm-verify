"""Centralized application configuration using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──
    database_url: str = "sqlite+aiosqlite:///./benchmarker.db"

    # ── AI Provider Keys ──
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    suspect_api_key: str = ""
    suspect_api_base_url: str = ""

    # ── Application ──
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    benchmark_timeout: int = 30
    max_concurrent_calls: int = 5

    @property
    def db_path(self) -> Path:
        """Extract the file path from the SQLite URL."""
        raw = self.database_url.replace("sqlite+aiosqlite:///", "")
        return Path(raw)


def get_settings() -> Settings:
    """Create and return a Settings instance (cached at call site via Depends)."""
    return Settings()
