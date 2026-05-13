"""Long-polling orchestration for the local Telegram worker."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from telegram_worker.client import RuntimeAgentNotFoundError
from telegram_worker.commands import TelegramCommandRouter
from telegram_worker.normalizer import normalize_update
from telegram_worker.settings import TelegramWorkerSettings
from telegram_worker.showcase import extract_trace_metadata, map_showcase_command

LOGGER = logging.getLogger(__name__)
UNSUPPORTED_MESSAGE = "This local demo bot only supports text messages."
EMPTY_ANSWER_MESSAGE = "The agent did not return an answer."
AGENT_NOT_FOUND_MESSAGE = (
    "The local Telegram worker is configured with an agent id that Runtime API "
    "does not know. Check GET /v1/agents and update TELEGRAM_AGENT_ID."
)


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


class TraceMetadataStore:
    """In-memory last-response metadata keyed by Telegram chat id."""

    def __init__(self) -> None:
        """Create an empty metadata store."""

        self._metadata_by_chat_id: dict[str, dict[str, str]] = {}

    def get(self, chat_id: int | str) -> dict[str, str] | None:
        """Return last metadata for a chat if available."""

        return self._metadata_by_chat_id.get(str(chat_id))

    def set(self, chat_id: int | str, metadata: dict[str, str]) -> None:
        """Store last metadata for a chat."""

        self._metadata_by_chat_id[str(chat_id)] = metadata


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
    command_router: TelegramCommandRouter | None = None,
    trace_store: TraceMetadataStore | None = None,
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

    chat_id = payload["metadata"]["telegram_chat_id"]
    router = command_router or TelegramCommandRouter()
    parsed = router.parse(str(payload["message"]))
    action = map_showcase_command(
        parsed,
        payload,
        last_trace=trace_store.get(chat_id) if trace_store is not None else None,
    )
    if action.local_response is not None:
        telegram_client.send_message(chat_id, action.local_response)
        return False

    runtime_payload = action.runtime_payload or payload
    try:
        response = runtime_client.invoke_agent(settings.telegram_agent_id, runtime_payload)
    except RuntimeAgentNotFoundError as exc:
        LOGGER.error(str(exc))
        telegram_client.send_message(chat_id, AGENT_NOT_FOUND_MESSAGE)
        return False

    answer = response.get("answer")
    text = answer if isinstance(answer, str) and answer.strip() else EMPTY_ANSWER_MESSAGE
    if trace_store is not None:
        trace_store.set(
            chat_id,
            extract_trace_metadata(
                response=response,
                runtime_payload=runtime_payload,
                agent_id=settings.telegram_agent_id,
            ),
        )
    telegram_client.send_message(chat_id, text)
    return True


def poll_once(
    *,
    telegram_client: TelegramClientProtocol,
    runtime_client: RuntimeApiClientProtocol,
    settings: TelegramWorkerSettings,
    offset: int | None,
    command_router: TelegramCommandRouter | None = None,
    trace_store: TraceMetadataStore | None = None,
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
            command_router=command_router,
            trace_store=trace_store,
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
    command_router = TelegramCommandRouter()
    trace_store = TraceMetadataStore()
    while True:
        offset = poll_once(
            telegram_client=telegram_client,
            runtime_client=runtime_client,
            settings=settings,
            offset=offset,
            command_router=command_router,
            trace_store=trace_store,
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
