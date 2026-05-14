"""Tests for memo memory contracts and in-memory store."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from snp_agent_memory import InMemoryMemoStore, MemoNotFoundError, MemoRecord, MemoScope


def _memo(key: str = "booking", value: str = "BK123") -> MemoRecord:
    now = datetime.now(UTC)
    return MemoRecord(
        key=key,
        value=value,
        scope=MemoScope.THREAD,
        tenant_id="demo",
        user_id="telegram:123456",
        thread_id="telegram:123456",
        created_at=now,
        updated_at=now,
        metadata={"source": "test"},
    )


def test_memo_record_validates() -> None:
    record = _memo()

    assert record.key == "booking"
    assert record.scope == MemoScope.THREAD
    assert record.created_at.utcoffset() == UTC.utcoffset(record.created_at)


def test_memo_record_rejects_blank_key() -> None:
    with pytest.raises(ValidationError):
        _memo(key=" ")


def test_memo_record_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError):
        MemoRecord(
            key="booking",
            value="BK123",
            scope=MemoScope.THREAD,
            tenant_id="demo",
            user_id="telegram:123456",
            thread_id="telegram:123456",
            created_at=datetime(2026, 5, 14, 8, 0, 0),
            updated_at=datetime.now(UTC),
        )


def test_in_memory_memo_store_remember_get_and_list() -> None:
    store = InMemoryMemoStore()
    record = store.remember(_memo())

    assert store.get("booking", "demo", "telegram:123456", "telegram:123456") == record
    assert store.list_memos("demo", "telegram:123456", "telegram:123456") == [record]


def test_in_memory_memo_store_overwrites_existing_key() -> None:
    store = InMemoryMemoStore()
    original = store.remember(_memo(value="BK123"))
    updated = store.remember(_memo(value="BK999"))

    assert updated.value == "BK999"
    assert updated.created_at == original.created_at
    assert updated.updated_at >= original.updated_at
    assert store.list_memos("demo", "telegram:123456", "telegram:123456") == [updated]


def test_in_memory_memo_store_forget_removes_memo() -> None:
    store = InMemoryMemoStore()
    store.remember(_memo())

    store.forget("booking", "demo", "telegram:123456", "telegram:123456")

    assert store.list_memos("demo", "telegram:123456", "telegram:123456") == []


def test_in_memory_memo_store_unknown_key_raises_clear_error() -> None:
    store = InMemoryMemoStore()

    with pytest.raises(MemoNotFoundError, match=r"Memo 'booking' was not found\."):
        store.get("booking", "demo", "telegram:123456", "telegram:123456")


def test_snp_agent_memory_does_not_import_apps() -> None:
    package_dir = Path("packages/snp_agent_memory/src/snp_agent_memory")
    source = "\n".join(path.read_text() for path in package_dir.glob("*.py"))

    assert "telegram_worker" not in source
    assert "apps." not in source
