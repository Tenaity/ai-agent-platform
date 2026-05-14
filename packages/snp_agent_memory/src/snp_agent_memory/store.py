"""Memo memory store interfaces and local in-memory implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from snp_agent_memory.contracts import MemoRecord


class MemoStoreError(RuntimeError):
    """Base error for memo store operations."""


class MemoNotFoundError(MemoStoreError):
    """Raised when a memo key does not exist in the requested scope."""


class MemoStore(ABC):
    """Abstract persistence boundary for small scoped memo records."""

    @abstractmethod
    def remember(self, record: MemoRecord) -> MemoRecord:
        """Create or update a memo record."""

    @abstractmethod
    def get(
        self,
        key: str,
        tenant_id: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> MemoRecord:
        """Return a memo record by key and scope identity."""

    @abstractmethod
    def forget(
        self,
        key: str,
        tenant_id: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> None:
        """Delete a memo record by key and scope identity."""

    @abstractmethod
    def list_memos(
        self,
        tenant_id: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> list[MemoRecord]:
        """List memos in insertion order for the requested scope identity."""


class InMemoryMemoStore(MemoStore):
    """Local/demo memo store backed by process memory."""

    def __init__(self) -> None:
        """Create an empty in-memory memo store."""

        self._records: dict[tuple[str, str, str | None, str], MemoRecord] = {}

    def remember(self, record: MemoRecord) -> MemoRecord:
        """Create or overwrite a memo while preserving insertion order."""

        store_key = _store_key(
            key=record.key,
            tenant_id=record.tenant_id,
            user_id=record.user_id,
            thread_id=record.thread_id,
        )
        existing = self._records.get(store_key)
        if existing is None:
            self._records[store_key] = record
            return record

        update: dict[str, Any] = record.model_dump()
        update["created_at"] = existing.created_at
        update["updated_at"] = datetime.now(UTC)
        updated = MemoRecord.model_validate(update)
        self._records[store_key] = updated
        return updated

    def get(
        self,
        key: str,
        tenant_id: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> MemoRecord:
        """Return a memo record or raise a clear error."""

        store_key = _store_key(
            key=key,
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
        )
        try:
            return self._records[store_key]
        except KeyError:
            raise MemoNotFoundError(f"Memo '{key.strip()}' was not found.") from None

    def forget(
        self,
        key: str,
        tenant_id: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> None:
        """Delete a memo record or raise a clear error."""

        store_key = _store_key(
            key=key,
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
        )
        try:
            del self._records[store_key]
        except KeyError:
            raise MemoNotFoundError(f"Memo '{key.strip()}' was not found.") from None

    def list_memos(
        self,
        tenant_id: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> list[MemoRecord]:
        """List memo records in insertion order."""

        tenant = _required(tenant_id, "tenant_id")
        user = _required(user_id, "user_id")
        normalized_thread = _optional(thread_id)
        return [
            record
            for (record_tenant, record_user, record_thread, _), record in self._records.items()
            if record_tenant == tenant
            and record_user == user
            and record_thread == normalized_thread
        ]


def _store_key(
    *,
    key: str,
    tenant_id: str,
    user_id: str,
    thread_id: str | None,
) -> tuple[str, str, str | None, str]:
    return (
        _required(tenant_id, "tenant_id"),
        _required(user_id, "user_id"),
        _optional(thread_id),
        _required(key, "key"),
    )


def _required(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be blank")
    return stripped


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
