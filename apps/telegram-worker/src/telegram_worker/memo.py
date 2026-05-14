"""Telegram-facing memo showcase service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from snp_agent_memory import InMemoryMemoStore, MemoNotFoundError, MemoRecord, MemoScope, MemoStore
from telegram_worker.commands import ParsedTelegramCommand, TelegramCommand


class TelegramMemoService:
    """Local Telegram demo service for thread-scoped memo commands."""

    def __init__(self, store: MemoStore | None = None) -> None:
        """Create a service backed by the provided memo store."""

        self._store = store or InMemoryMemoStore()

    def handle(
        self,
        parsed: ParsedTelegramCommand,
        *,
        runtime_payload: dict[str, Any],
    ) -> str | None:
        """Return a local response for memo commands, or `None` if not handled."""

        if parsed.command != TelegramCommand.MEMO:
            return None

        subcommand, _, rest = parsed.args.strip().partition(" ")
        match subcommand.casefold():
            case "remember":
                return self._remember(rest, runtime_payload=runtime_payload)
            case "get":
                return self._get(rest, runtime_payload=runtime_payload)
            case "forget":
                return self._forget(rest, runtime_payload=runtime_payload)
            case "list":
                return self._list(runtime_payload=runtime_payload)
            case "":
                return "Usage: /memo remember <key> <value> | /memo get <key> | /memo list"
            case _:
                key = _resolve_question_key(parsed.args)
                if key is None:
                    return "I can answer simple memo questions such as: /memo what is my booking?"
                return self._get(key, runtime_payload=runtime_payload)

    def _remember(self, args: str, *, runtime_payload: dict[str, Any]) -> str:
        key, _, value = args.strip().partition(" ")
        if not key.strip() or not value.strip():
            return "Usage: /memo remember <key> <value>"

        now = datetime.now(UTC)
        record = MemoRecord(
            key=key,
            value=value,
            scope=MemoScope.THREAD,
            tenant_id=str(runtime_payload["tenant_id"]),
            user_id=str(runtime_payload["user_id"]),
            thread_id=str(runtime_payload["thread_id"]),
            created_at=now,
            updated_at=now,
            metadata=_safe_telegram_metadata(runtime_payload),
        )
        saved = self._store.remember(record)
        return f"Remembered memo: {saved.key}={saved.value}"

    def _get(self, key: str, *, runtime_payload: dict[str, Any]) -> str:
        memo_key = key.strip()
        if not memo_key:
            return "Usage: /memo get <key>"
        try:
            record = self._store.get(
                memo_key,
                tenant_id=str(runtime_payload["tenant_id"]),
                user_id=str(runtime_payload["user_id"]),
                thread_id=str(runtime_payload["thread_id"]),
            )
        except MemoNotFoundError as exc:
            return str(exc)
        return f"{record.key}={record.value}"

    def _forget(self, key: str, *, runtime_payload: dict[str, Any]) -> str:
        memo_key = key.strip()
        if not memo_key:
            return "Usage: /memo forget <key>"
        try:
            self._store.forget(
                memo_key,
                tenant_id=str(runtime_payload["tenant_id"]),
                user_id=str(runtime_payload["user_id"]),
                thread_id=str(runtime_payload["thread_id"]),
            )
        except MemoNotFoundError as exc:
            return str(exc)
        return f"Forgot memo: {memo_key}"

    def _list(self, *, runtime_payload: dict[str, Any]) -> str:
        records = self._store.list_memos(
            tenant_id=str(runtime_payload["tenant_id"]),
            user_id=str(runtime_payload["user_id"]),
            thread_id=str(runtime_payload["thread_id"]),
        )
        if not records:
            return "No memos for this thread."
        lines = ["Thread memos:"]
        lines.extend(f"- {record.key}={record.value}" for record in records)
        return "\n".join(lines)


def _resolve_question_key(args: str) -> str | None:
    normalized = args.casefold()
    if "booking" in normalized:
        return "booking"
    return None


def _safe_telegram_metadata(runtime_payload: dict[str, Any]) -> dict[str, Any]:
    metadata = runtime_payload.get("metadata")
    if not isinstance(metadata, dict):
        return {"source": "telegram_showcase"}

    safe_keys = {
        "telegram_update_id",
        "telegram_chat_id",
        "telegram_message_id",
        "telegram_username",
    }
    safe_metadata = {
        key: value
        for key, value in metadata.items()
        if key in safe_keys and isinstance(value, str | int)
    }
    safe_metadata["source"] = "telegram_showcase"
    return safe_metadata
