"""Tests for Telegram skills showcase commands."""

from __future__ import annotations

from typing import Any

from snp_agent_core.skills import SkillRegistry, SkillSpec, SkillStep
from telegram_worker.polling import process_update
from telegram_worker.settings import TelegramWorkerSettings
from telegram_worker.skills import TelegramSkillsService


class FakeTelegramClient:
    """In-memory Telegram client for skills command tests."""

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


def _registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(
        SkillSpec(
            id="demo_skill",
            name="Demo Skill",
            description="Reusable demo workflow template.",
            version="0.1.0",
            domain="demo",
            steps=[
                SkillStep(
                    id="step_one",
                    title="Step one",
                    description="First deterministic step.",
                ),
                SkillStep(
                    id="step_two",
                    title="Step two",
                    description="Second deterministic step.",
                ),
            ],
        )
    )
    return registry


def test_skill_list_returns_available_skills_without_runtime_call() -> None:
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()

    processed = process_update(
        _text_update("/skill list"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
        skills_service=TelegramSkillsService(_registry()),
    )

    assert processed is False
    assert runtime_client.invocations == []
    assert "Available skills:" in telegram_client.sent_messages[0]["text"]
    assert "- demo_skill: Demo Skill" in telegram_client.sent_messages[0]["text"]


def test_skill_show_returns_metadata_and_steps() -> None:
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()

    process_update(
        _text_update("/skill show demo_skill"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
        skills_service=TelegramSkillsService(_registry()),
    )

    response = telegram_client.sent_messages[0]["text"]
    assert "Skill: demo_skill" in response
    assert "name=Demo Skill" in response
    assert "- step_one: Step one - First deterministic step." in response
    assert runtime_client.invocations == []


def test_skill_run_returns_deterministic_simulated_result() -> None:
    telegram_client = FakeTelegramClient()
    runtime_client = FakeRuntimeApiClient()

    process_update(
        _text_update("/skill run demo_skill"),
        telegram_client=telegram_client,
        runtime_client=runtime_client,
        settings=_settings(),
        skills_service=TelegramSkillsService(_registry()),
    )

    response = telegram_client.sent_messages[0]["text"]
    assert "Simulated skill run: demo_skill" in response
    assert "No LLM, tool, or external API was called." in response
    assert "- step_one: simulated" in response
    assert runtime_client.invocations == []
