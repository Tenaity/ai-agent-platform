"""HTTP clients used by the local Telegram polling worker."""

from __future__ import annotations

from typing import Any

import httpx


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
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data
