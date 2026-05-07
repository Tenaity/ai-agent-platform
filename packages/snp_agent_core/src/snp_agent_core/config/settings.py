"""Environment-backed settings for platform runtime processes."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="SNP_", env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
