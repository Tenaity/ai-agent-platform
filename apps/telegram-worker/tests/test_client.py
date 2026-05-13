"""Tests for Telegram and Runtime API clients."""

from __future__ import annotations

import logging
from typing import Any

import httpx
import pytest

from telegram_worker.client import (
    RuntimeAgentNotFoundError,
    RuntimeApiClient,
    install_httpx_token_redaction,
)


def test_runtime_client_raises_clear_agent_not_found_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "not found"}, request=request)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = RuntimeApiClient(base_url="http://localhost:8000", http_client=http_client)

    with pytest.raises(RuntimeAgentNotFoundError) as exc_info:
        client.invoke_agent("missing_agent", {"message": "hello"})

    assert "missing_agent" in str(exc_info.value)
    assert "GET /v1/agents" in str(exc_info.value)


def test_httpx_log_redaction_removes_telegram_bot_token(caplog: Any) -> None:
    token = "123456:secret-token"
    install_httpx_token_redaction(token)
    logger = logging.getLogger("httpx")

    with caplog.at_level(logging.INFO, logger="httpx"):
        logger.info("POST https://api.telegram.org/bot%s/getUpdates", token)

    assert token not in caplog.text
    assert "[REDACTED_TELEGRAM_BOT_TOKEN]" in caplog.text
