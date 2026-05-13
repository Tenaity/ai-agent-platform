"""Tests for Telegram human-in-the-loop showcase commands."""

from __future__ import annotations

from typing import Any

from snp_agent_core.human_loop import ApprovalStatus, InMemoryApprovalStore
from telegram_worker.human_loop import TelegramHumanLoopService
from telegram_worker.polling import process_update
from telegram_worker.settings import TelegramWorkerSettings


class FakeTelegramClient:
    """In-memory Telegram client for HITL command tests."""

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


def test_human_command_creates_pending_approval_without_runtime_call() -> None:
    store = InMemoryApprovalStore()
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()

    processed = process_update(
        _text_update("/human yêu cầu hoàn phí lưu bãi"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
        human_loop_service=TelegramHumanLoopService(store),
    )

    pending = store.list_pending()
    assert processed is False
    assert runtime_client.invocations == []
    assert len(pending) == 1
    assert pending[0].status == ApprovalStatus.PENDING
    assert pending[0].action_summary == "yêu cầu hoàn phí lưu bãi"
    assert "approval_id=" in telegram_client.sent_messages[0]["text"]


def test_approve_command_approves_pending_approval() -> None:
    store = InMemoryApprovalStore()
    service = TelegramHumanLoopService(store)
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    settings = _settings()

    process_update(
        _text_update("/human yêu cầu hoàn phí"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        human_loop_service=service,
    )
    approval_id = store.list_pending()[0].approval_id
    process_update(
        _text_update(f"/approve {approval_id}"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        human_loop_service=service,
    )

    assert store.get(approval_id).status == ApprovalStatus.APPROVED
    assert store.list_pending() == []
    assert "status=approved" in telegram_client.sent_messages[-1]["text"]
    assert runtime_client.invocations == []


def test_reject_command_rejects_pending_approval() -> None:
    store = InMemoryApprovalStore()
    service = TelegramHumanLoopService(store)
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    settings = _settings()

    process_update(
        _text_update("/human yêu cầu hoàn phí"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        human_loop_service=service,
    )
    approval_id = store.list_pending()[0].approval_id
    process_update(
        _text_update(f"/reject {approval_id}"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        human_loop_service=service,
    )

    assert store.get(approval_id).status == ApprovalStatus.REJECTED
    assert store.list_pending() == []
    assert "status=rejected" in telegram_client.sent_messages[-1]["text"]
    assert runtime_client.invocations == []


def test_approvals_command_lists_pending_approvals() -> None:
    store = InMemoryApprovalStore()
    service = TelegramHumanLoopService(store)
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()
    settings = _settings()

    process_update(
        _text_update("/human yêu cầu hoàn phí"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        human_loop_service=service,
    )
    approval_id = store.list_pending()[0].approval_id
    process_update(
        _text_update("/approvals"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=settings,
        human_loop_service=service,
    )

    assert approval_id in telegram_client.sent_messages[-1]["text"]
    assert "Pending approvals:" in telegram_client.sent_messages[-1]["text"]
    assert runtime_client.invocations == []
