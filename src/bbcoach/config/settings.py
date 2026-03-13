"""
BBCoach Configuration Management

Centralized configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # AI Configuration
    default_ai_provider: Literal["gemini", "openai", "anthropic", "local"] = "local"
    default_model_gemini: str = "gemini-2.0-flash"
    default_model_openai: str = "gpt-4o"
    default_model_anthropic: str = "claude-3-5-sonnet-latest"

    # Data Paths
    data_dir: str = "data_storage"
    vector_db_dir: str = ".vectordb"

    # Scraper Configuration
    scraper_timeout: int = 60
    scraper_delay: float = 1.0  # Delay between requests
    max_concurrent_requests: int = 3

    # Competitions Configuration
    competitions: list[dict] = [
        {"id": 41539, "name": "SBL Herr", "year": 2025, "league": "Men"},
    ]

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
