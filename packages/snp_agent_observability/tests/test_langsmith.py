"""Tests for optional LangSmith configuration."""

import os
from typing import Any

from snp_agent_observability import LangSmithSettings, configure_langsmith


def test_configure_langsmith_disabled_mode_does_not_set_env(monkeypatch: Any) -> None:
    """Disabled tracing does not require credentials or mutate LangSmith env vars."""

    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_ENDPOINT", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    configure_langsmith(
        LangSmithSettings(
            langsmith_tracing=False,
            langsmith_endpoint=None,
            langsmith_api_key="secret-test-key",
            langsmith_project=None,
            snp_trace_sample_rate=1.0,
        )
    )

    assert "LANGSMITH_TRACING" not in os.environ
    assert "LANGSMITH_API_KEY" not in os.environ
