"""Normalize Telegram updates into Runtime API request payloads."""

from __future__ import annotations

from typing import Any

from snp_agent_core.contracts import RuntimeRequest


def normalize_update(
    update: dict[str, Any],
    *,
    tenant_id: str,
) -> dict[str, Any] | None:
    """Convert a Telegram text update into a RuntimeRequest-compatible payload.

    Non-message updates, missing text, and blank text are ignored by returning
    `None`. The worker can then safely skip them without failing the polling
    loop or calling the Runtime API.
    """

    message = update.get("message")
    if not isinstance(message, dict):
        return None

    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None

    chat_id = chat.get("id")
    if chat_id is None:
        return None

    metadata = _metadata_from_update(update, message, chat_id)
    request = RuntimeRequest(
        tenant_id=tenant_id,
        channel="telegram",
        user_id=f"telegram:{chat_id}",
        thread_id=f"telegram:{chat_id}",
        message=text,
        metadata=metadata,
    )
    return request.model_dump()


def _metadata_from_update(
    update: dict[str, Any],
    message: dict[str, Any],
    chat_id: Any,
) -> dict[str, Any]:
    """Extract Telegram metadata safe to pass through the runtime boundary."""

    metadata: dict[str, Any] = {
        "telegram_update_id": update.get("update_id"),
        "telegram_chat_id": chat_id,
        "telegram_message_id": message.get("message_id"),
    }

    sender = message.get("from")
    if isinstance(sender, dict):
        username = sender.get("username")
        if isinstance(username, str) and username.strip():
            metadata["telegram_username"] = username.strip()

    return metadata
