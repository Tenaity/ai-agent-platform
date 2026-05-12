"""Long-polling orchestration for the local Telegram worker."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from telegram_worker.normalizer import normalize_update
from telegram_worker.settings import TelegramWorkerSettings

LOGGER = logging.getLogger(__name__)
UNSUPPORTED_MESSAGE = "This local demo bot only supports text messages."
EMPTY_ANSWER_MESSAGE = "The agent did not return an answer."


class TelegramClientProtocol(Protocol):
    """Minimal Telegram operations required by the polling loop."""

    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        """Return Telegram updates."""

    def send_message(self, chat_id: int | str, text: str) -> dict[str, Any]:
        """Send a text message to Telegram."""


class RuntimeApiClientProtocol(Protocol):
    """Minimal Runtime API operation required by the polling loop."""

    def invoke_agent(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Invoke an agent via the Runtime API."""


def log_startup(settings: TelegramWorkerSettings) -> None:
    """Log startup metadata without exposing the Telegram bot token."""

    LOGGER.info(settings.safe_log_summary())


def process_update(
    update: dict[str, Any],
    *,
    telegram_client: TelegramClientProtocol,
    runtime_client: RuntimeApiClientProtocol,
    settings: TelegramWorkerSettings,
    reply_to_unsupported: bool = False,
) -> bool:
    """Process one Telegram update.

    Returns `True` when a text update was sent to the Runtime API and answered.
    Returns `False` for ignored unsupported updates.
    """

    payload = normalize_update(update, tenant_id=settings.telegram_tenant_id)
    if payload is None:
        if reply_to_unsupported:
            chat_id = _chat_id_from_update(update)
            if chat_id is not None:
                telegram_client.send_message(chat_id, UNSUPPORTED_MESSAGE)
        return False

    response = runtime_client.invoke_agent(settings.telegram_agent_id, payload)
    answer = response.get("answer")
    text = answer if isinstance(answer, str) and answer.strip() else EMPTY_ANSWER_MESSAGE
    chat_id = payload["metadata"]["telegram_chat_id"]
    telegram_client.send_message(chat_id, text)
    return True


def poll_once(
    *,
    telegram_client: TelegramClientProtocol,
    runtime_client: RuntimeApiClientProtocol,
    settings: TelegramWorkerSettings,
    offset: int | None,
) -> int | None:
    """Fetch one batch of updates, process them, and return the next offset."""

    updates = telegram_client.get_updates(
        offset=offset,
        timeout=settings.telegram_poll_timeout_seconds,
    )
    next_offset = offset
    for update in updates:
        process_update(
            update,
            telegram_client=telegram_client,
            runtime_client=runtime_client,
            settings=settings,
        )
        update_id = update.get("update_id")
        if isinstance(update_id, int):
            candidate = update_id + 1
            next_offset = candidate if next_offset is None else max(next_offset, candidate)
    return next_offset


def run_polling(
    *,
    telegram_client: TelegramClientProtocol,
    runtime_client: RuntimeApiClientProtocol,
    settings: TelegramWorkerSettings,
) -> None:
    """Run Telegram getUpdates polling until the process is interrupted."""

    log_startup(settings)
    offset: int | None = None
    while True:
        offset = poll_once(
            telegram_client=telegram_client,
            runtime_client=runtime_client,
            settings=settings,
            offset=offset,
        )


def _chat_id_from_update(update: dict[str, Any]) -> int | str | None:
    """Return a chat ID from an unsupported update if one is present."""

    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = chat.get("id")
    if isinstance(chat_id, int | str):
        return chat_id
    return None
