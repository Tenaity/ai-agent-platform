"""LangSmith tracing configuration for platform runtime processes."""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LangSmithSettings(BaseSettings):
    """Environment-backed settings for optional LangSmith tracing."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    langsmith_tracing: bool = Field(default=False, validation_alias="LANGSMITH_TRACING")
    langsmith_endpoint: str | None = Field(default=None, validation_alias="LANGSMITH_ENDPOINT")
    langsmith_api_key: str | None = Field(default=None, validation_alias="LANGSMITH_API_KEY")
    langsmith_project: str | None = Field(default=None, validation_alias="LANGSMITH_PROJECT")
    snp_trace_sample_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        validation_alias="SNP_TRACE_SAMPLE_RATE",
    )


def configure_langsmith(settings: LangSmithSettings) -> None:
    """Configure LangSmith environment variables when tracing is explicitly enabled.

    Local tests and development must not require credentials. When tracing is
    disabled, this function exits without setting LangSmith variables or
    contacting the network. Secrets are copied only into process environment
    variables and are never printed or returned.
    """

    if not settings.langsmith_tracing:
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    if settings.langsmith_project:
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
