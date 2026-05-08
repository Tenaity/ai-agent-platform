"""Environment-backed settings for platform runtime processes."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from snp_agent_core.checkpointing.config import CheckpointBackend


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="SNP_", env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"
    checkpoint_backend: CheckpointBackend = CheckpointBackend.NONE
    checkpoint_namespace: str | None = None
