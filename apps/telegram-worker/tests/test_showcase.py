"""Tests for Telegram showcase command mapping."""

from telegram_worker.commands import TelegramCommandRouter
from telegram_worker.showcase import (
    HELP_RESPONSE,
    SHOWCASE_RESPONSE,
    format_trace_response,
    map_showcase_command,
)


def _payload(message: str) -> dict[str, object]:
    return {
        "tenant_id": "demo",
        "channel": "telegram",
        "user_id": "telegram:123456",
        "thread_id": "telegram:123456",
        "message": message,
        "metadata": {"telegram_chat_id": 123456},
    }


def test_help_returns_local_response() -> None:
    parsed = TelegramCommandRouter().parse("/help")
    action = map_showcase_command(parsed, _payload("/help"))

    assert action.local_response == HELP_RESPONSE
    assert action.runtime_payload is None


def test_showcase_returns_demo_script() -> None:
    parsed = TelegramCommandRouter().parse("/showcase")
    action = map_showcase_command(parsed, _payload("/showcase"))

    assert action.local_response == SHOWCASE_RESPONSE
    assert "/tool container ABCD1234567" in action.local_response


def test_placeholder_commands_return_local_response() -> None:
    parsed = TelegramCommandRouter().parse("/mcp list")
    action = map_showcase_command(parsed, _payload("/mcp list"))

    assert action.local_response == "MCP showcase is planned for PR-027."
    assert action.runtime_payload is None


def test_rag_maps_to_runtime_request_payload() -> None:
    parsed = TelegramCommandRouter().parse("/rag giờ làm việc")
    action = map_showcase_command(parsed, _payload("/rag giờ làm việc"))

    assert action.runtime_payload is not None
    assert action.runtime_payload["message"] == "chính sách giờ làm việc"
    assert action.local_response is None


def test_tool_container_maps_to_runtime_request_payload() -> None:
    parsed = TelegramCommandRouter().parse("/tool container ABCD1234567")
    action = map_showcase_command(parsed, _payload("/tool container ABCD1234567"))

    assert action.runtime_payload is not None
    assert action.runtime_payload["message"] == "tracking container ABCD1234567"
    assert action.local_response is None


def test_booking_maps_to_runtime_request_payload() -> None:
    parsed = TelegramCommandRouter().parse("/booking BK123")
    action = map_showcase_command(parsed, _payload("/booking BK123"))

    assert action.runtime_payload is not None
    assert action.runtime_payload["message"] == "booking BK123"


def test_ticket_maps_to_runtime_request_payload() -> None:
    parsed = TelegramCommandRouter().parse("/ticket Tôi cần hỗ trợ")
    action = map_showcase_command(parsed, _payload("/ticket Tôi cần hỗ trợ"))

    assert action.runtime_payload is not None
    assert action.runtime_payload["message"] == "ticket Tôi cần hỗ trợ"


def test_trace_returns_last_metadata_when_available() -> None:
    response = format_trace_response(
        {
            "last_request_id": "req_123",
            "last_run_id": "run_456",
            "last_thread_id": "telegram:123456",
            "last_agent_id": "customer_service",
        }
    )

    assert "request_id=req_123" in response
    assert "run_id=run_456" in response
    assert "thread_id=telegram:123456" in response
    assert "agent_id=customer_service" in response
