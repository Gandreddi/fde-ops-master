"""Settings read from environment variables that start with OPS_ (or from a .env file)."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPS_", env_file=".env", extra="ignore")

    base_url: str = "https://jsonplaceholder.typicode.com"  # OPS_BASE_URL
    timeout_seconds: float = Field(default=10.0, gt=0)  # OPS_TIMEOUT_SECONDS
    max_attempts: int = Field(default=3, ge=1)  # OPS_MAX_ATTEMPTS
    log_level: str = "WARNING"  # OPS_LOG_LEVEL
