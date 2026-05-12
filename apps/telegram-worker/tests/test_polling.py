"""Tests for Telegram polling orchestration."""

from __future__ import annotations

import logging
from typing import Any

from telegram_worker.polling import log_startup, poll_once, process_update
from telegram_worker.settings import TelegramWorkerSettings


class FakeTelegramClient:
    """In-memory Telegram client used to prove tests make no API calls."""

    def __init__(self, updates: list[dict[str, Any]] | None = None) -> None:
        self.updates = updates or []
        self.get_update_calls: list[dict[str, Any]] = []
        self.sent_messages: list[dict[str, Any]] = []

    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        self.get_update_calls.append({"offset": offset, "timeout": timeout})
        return self.updates

    def send_message(self, chat_id: int | str, text: str) -> dict[str, Any]:
        self.sent_messages.append({"chat_id": chat_id, "text": text})
        return {"ok": True, "result": {"chat_id": chat_id, "text": text}}


class FakeRuntimeApiClient:
    """In-memory Runtime API client used to prove the worker calls the API boundary."""

    def __init__(self, answer: str = "Agent answer") -> None:
        self.answer = answer
        self.invocations: list[dict[str, Any]] = []

    def invoke_agent(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.invocations.append({"agent_id": agent_id, "payload": payload})
        return {"thread_id": payload["thread_id"], "status": "completed", "answer": self.answer}


def _settings(**overrides: Any) -> TelegramWorkerSettings:
    values = {
        "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_AGENT_ID": "customer_service",
        "TELEGRAM_TENANT_ID": "demo",
        "RUNTIME_API_BASE_URL": "http://localhost:8000",
        "TELEGRAM_POLL_TIMEOUT_SECONDS": 1,
    }
    values.update(overrides)
    return TelegramWorkerSettings.model_validate(values)


def _text_update(update_id: int = 1001) -> dict[str, Any]:
    return {
        "update_id": update_id,
        "message": {
            "message_id": 55,
            "text": "giờ làm việc hỗ trợ là gì?",
            "chat": {"id": 123456},
            "from": {"username": "demo_user"},
        },
    }


def test_process_update_calls_runtime_api_client_and_sends_answer() -> None:
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient(answer="Support is open 08:00-17:00.")

    processed = process_update(
        _text_update(),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
    )

    assert processed is True
    assert runtime_client.invocations[0]["agent_id"] == "customer_service"
    assert runtime_client.invocations[0]["payload"]["channel"] == "telegram"
    assert telegram_client.sent_messages == [
        {"chat_id": 123456, "text": "Support is open 08:00-17:00."}
    ]


def test_process_update_ignores_missing_text_without_runtime_call() -> None:
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    update = {"update_id": 1002, "message": {"chat": {"id": 123456}, "message_id": 56}}

    processed = process_update(
        update,
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
    )

    assert processed is False
    assert runtime_client.invocations == []
    assert telegram_client.sent_messages == []


def test_poll_once_tracks_offset_and_uses_fake_clients_only() -> None:
    telegram_client = FakeTelegramClient(updates=[_text_update(update_id=200)])
    runtime_client = FakeRuntimeApiClient(answer="Done")

    next_offset = poll_once(
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
        offset=None,
    )

    assert next_offset == 201
    assert telegram_client.get_update_calls == [{"offset": None, "timeout": 1}]
    assert len(runtime_client.invocations) == 1
    assert telegram_client.sent_messages == [{"chat_id": 123456, "text": "Done"}]


def test_bot_token_is_not_logged(caplog: Any) -> None:
    settings = _settings(TELEGRAM_BOT_TOKEN="secret-token-value")

    with caplog.at_level(logging.INFO):
        log_startup(settings)

    assert "secret-token-value" not in caplog.text
    assert "customer_service" in caplog.text
