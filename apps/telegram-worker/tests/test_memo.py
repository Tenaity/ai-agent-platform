"""Tests for Telegram memo showcase commands."""

from __future__ import annotations

from typing import Any

from snp_agent_memory import InMemoryMemoStore
from telegram_worker.memo import TelegramMemoService
from telegram_worker.polling import process_update
from telegram_worker.settings import TelegramWorkerSettings


class FakeTelegramClient:
    """In-memory Telegram client for memo command tests."""

    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []

    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        return []

    def send_message(self, chat_id: int | str, text: str) -> dict[str, Any]:
        self.sent_messages.append({"chat_id": chat_id, "text": text})
        return {"ok": True, "result": {"chat_id": chat_id, "text": text}}


class FakeRuntimeApiClient:
    """Runtime fake that records whether the worker crossed the API boundary."""

    def __init__(self) -> None:
        self.invocations: list[dict[str, Any]] = []

    def invoke_agent(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.invocations.append({"agent_id": agent_id, "payload": payload})
        return {"answer": "unexpected"}


def _settings() -> TelegramWorkerSettings:
    return TelegramWorkerSettings.model_validate(
        {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_AGENT_ID": "customer_service",
            "TELEGRAM_TENANT_ID": "demo",
            "RUNTIME_API_BASE_URL": "http://localhost:8000",
            "TELEGRAM_POLL_TIMEOUT_SECONDS": 1,
        }
    )


def _text_update(text: str) -> dict[str, Any]:
    return {
        "update_id": 1001,
        "message": {
            "message_id": 55,
            "text": text,
            "chat": {"id": 123456},
            "from": {"username": "demo_user"},
        },
    }


def test_memo_remember_stores_value_without_runtime_call() -> None:
    store = InMemoryMemoStore()
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()

    processed = process_update(
        _text_update("/memo remember booking BK123"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
        memo_service=TelegramMemoService(store),
    )

    assert processed is False
    assert runtime_client.invocations == []
    assert "Remembered memo: booking=BK123" in telegram_client.sent_messages[0]["text"]
    assert (
        store.get("booking", "demo", "telegram:123456", "telegram:123456").value
        == "BK123"
    )


def test_memo_get_returns_value() -> None:
    store = InMemoryMemoStore()
    service = TelegramMemoService(store)
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    settings = _settings()

    process_update(
        _text_update("/memo remember booking BK123"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )
    process_update(
        _text_update("/memo get booking"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )

    assert telegram_client.sent_messages[-1]["text"] == "booking=BK123"
    assert runtime_client.invocations == []


def test_memo_list_lists_values() -> None:
    store = InMemoryMemoStore()
    service = TelegramMemoService(store)
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    settings = _settings()

    process_update(
        _text_update("/memo remember booking BK123"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )
    process_update(
        _text_update("/memo list"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )

    assert "Thread memos:" in telegram_client.sent_messages[-1]["text"]
    assert "- booking=BK123" in telegram_client.sent_messages[-1]["text"]
    assert runtime_client.invocations == []


def test_memo_forget_deletes_value() -> None:
    store = InMemoryMemoStore()
    service = TelegramMemoService(store)
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    settings = _settings()

    process_update(
        _text_update("/memo remember booking BK123"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )
    process_update(
        _text_update("/memo forget booking"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )

    assert telegram_client.sent_messages[-1]["text"] == "Forgot memo: booking"
    assert store.list_memos("demo", "telegram:123456", "telegram:123456") == []
    assert runtime_client.invocations == []


def test_memo_question_returns_booking_if_present() -> None:
    store = InMemoryMemoStore()
    service = TelegramMemoService(store)
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    settings = _settings()

    process_update(
        _text_update("/memo remember booking BK123"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )
    process_update(
        _text_update("/memo what is my booking?"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        memo_service=service,
    )

    assert telegram_client.sent_messages[-1]["text"] == "booking=BK123"
    assert runtime_client.invocations == []
