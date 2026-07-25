"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment variables.

    All fields have sensible defaults so the application can start
    without any configuration for local development.
    """

    # Redis
    redis_url: str | None = None

    # Cache
    cache_ttl: int = 300

    # HTTP client
    request_timeout: float = 10.0
    max_concurrent_requests: int = 10

    # Rate limiting
    rate_limit: str = "10/minute"

    # Logging
    log_level: str = "INFO"

    # Environment
    environment: str = "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
