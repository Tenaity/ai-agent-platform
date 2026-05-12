"""Settings for the local Telegram polling worker."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramWorkerSettings(BaseSettings):
    """Environment-backed configuration for the local Telegram demo worker.

    The bot token is intentionally not included in any derived display helpers.
    Worker logs should identify the runtime target and agent, never the token.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_poll_timeout_seconds: int = Field(
        default=30,
        gt=0,
        alias="TELEGRAM_POLL_TIMEOUT_SECONDS",
    )
    telegram_agent_id: str = Field(default="customer_service", alias="TELEGRAM_AGENT_ID")
    runtime_api_base_url: str = Field(
        default="http://localhost:8000",
        alias="RUNTIME_API_BASE_URL",
    )
    telegram_tenant_id: str = Field(default="demo", alias="TELEGRAM_TENANT_ID")

    @field_validator("telegram_agent_id", "runtime_api_base_url", "telegram_tenant_id")
    @classmethod
    def reject_blank_required_settings(cls, value: str) -> str:
        """Reject blank local routing settings while preserving surrounding semantics."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("setting must not be blank")
        return stripped

    @property
    def runtime_invoke_url(self) -> str:
        """Return the Runtime API invoke endpoint for the configured agent."""

        return (
            f"{self.runtime_api_base_url.rstrip('/')}"
            f"/v1/agents/{self.telegram_agent_id}/invoke"
        )

    def safe_log_summary(self) -> str:
        """Return startup metadata without exposing the Telegram bot token."""

        return (
            "telegram worker starting "
            f"agent_id={self.telegram_agent_id} "
            f"runtime_api_base_url={self.runtime_api_base_url.rstrip('/')} "
            f"tenant_id={self.telegram_tenant_id} "
            f"poll_timeout_seconds={self.telegram_poll_timeout_seconds}"
        )
