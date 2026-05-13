"""HTTP clients used by the local Telegram polling worker."""

from __future__ import annotations

import logging
from typing import Any, cast

import httpx

_REDACTED_TOKEN = "[REDACTED_TELEGRAM_BOT_TOKEN]"


class RuntimeAgentNotFoundError(RuntimeError):
    """Raised when the configured agent id is not registered in Runtime API."""

    def __init__(self, agent_id: str) -> None:
        """Create a safe, actionable 404 error."""

        super().__init__(
            f"Runtime API agent_id '{agent_id}' was not found. "
            "Verify available agents with GET /v1/agents before running the worker."
        )
        self.agent_id = agent_id


class TelegramTokenRedactionFilter(logging.Filter):
    """Redact the Telegram bot token from log records before they are emitted."""

    def __init__(self, token: str) -> None:
        """Create a filter for a single bot token."""

        super().__init__()
        self._token = token

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact token occurrences from message templates and arguments."""

        if not self._token:
            return True
        if isinstance(record.msg, str):
            record.msg = _redact_token(record.msg, self._token)
        if record.args:
            record.args = cast(Any, _redact_args(record.args, self._token))
        return True


def install_httpx_token_redaction(token: str) -> None:
    """Install log redaction for httpx/httpcore messages that may include bot URLs."""

    if not token:
        return
    for logger_name in ("httpx", "httpcore"):
        logger = logging.getLogger(logger_name)
        if not _has_redaction_filter(logger, token):
            logger.addFilter(TelegramTokenRedactionFilter(token))


def _has_redaction_filter(logger: logging.Logger, token: str) -> bool:
    """Return whether the logger already redacts this token."""

    return any(
        isinstance(log_filter, TelegramTokenRedactionFilter)
        and log_filter._token == token
        for log_filter in logger.filters
    )


def _redact_args(args: object, token: str) -> object:
    """Redact token occurrences from logging args without changing their shape."""

    if isinstance(args, str):
        return _redact_token(args, token)
    if isinstance(args, tuple):
        return tuple(_redact_args(item, token) for item in args)
    if isinstance(args, dict):
        return {key: _redact_args(value, token) for key, value in args.items()}
    return args


def _redact_token(value: str, token: str) -> str:
    """Return a string with the Telegram bot token replaced."""

    return value.replace(token, _REDACTED_TOKEN)


class TelegramClient:
    """Minimal Telegram Bot API client for local long polling.

    The token is used only to construct Telegram API URLs. Callers must not log
    the URL because it contains the bot token.
    """

    def __init__(
        self,
        *,
        bot_token: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Create the Telegram client with an injectable HTTP transport."""

        self._bot_token = bot_token
        self._http_client = http_client or httpx.Client(timeout=60)
        install_httpx_token_redaction(bot_token)

    def get_updates(
        self,
        offset: int | None,
        timeout: int,
    ) -> list[dict[str, Any]]:
        """Call Telegram `getUpdates` and return update objects."""

        payload: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset

        try:
            response = self._http_client.post(self._method_url("getUpdates"), json=payload)
        except httpx.HTTPError:
            raise RuntimeError("Telegram getUpdates request failed") from None
        if response.status_code >= 400:
            raise RuntimeError("Telegram getUpdates returned an HTTP error")
        data = response.json()
        if not data.get("ok", False):
            raise RuntimeError("Telegram getUpdates returned ok=false")
        result = data.get("result", [])
        if not isinstance(result, list):
            raise RuntimeError("Telegram getUpdates returned a non-list result")
        return [update for update in result if isinstance(update, dict)]

    def send_message(self, chat_id: int | str, text: str) -> dict[str, Any]:
        """Call Telegram `sendMessage` for a chat."""

        try:
            response = self._http_client.post(
                self._method_url("sendMessage"),
                json={"chat_id": chat_id, "text": text},
            )
        except httpx.HTTPError:
            raise RuntimeError("Telegram sendMessage request failed") from None
        if response.status_code >= 400:
            raise RuntimeError("Telegram sendMessage returned an HTTP error")
        data: dict[str, Any] = response.json()
        if not data.get("ok", False):
            raise RuntimeError("Telegram sendMessage returned ok=false")
        return data

    def _method_url(self, method: str) -> str:
        """Return a Telegram method URL. Do not log this value."""

        return f"https://api.telegram.org/bot{self._bot_token}/{method}"


class RuntimeApiClient:
    """Small client for invoking the platform Runtime API boundary."""

    def __init__(
        self,
        *,
        base_url: str,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Create the Runtime API client with an injectable HTTP transport."""

        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.Client(timeout=60)

    def invoke_agent(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST a RuntimeRequest-compatible payload to the Runtime API."""

        response = self._http_client.post(
            f"{self._base_url}/v1/agents/{agent_id}/invoke",
            json=payload,
        )
        if response.status_code == 404:
            raise RuntimeAgentNotFoundError(agent_id)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data
