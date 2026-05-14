"""Showcase command mapping for Telegram worker messages.

This module keeps Telegram command handling transport-oriented. It either
returns a local explanatory response for planned capabilities or rewrites a
RuntimeRequest-compatible payload so the existing agent graph owns behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from telegram_worker.commands import ParsedTelegramCommand, TelegramCommand

HELP_RESPONSE = """Commands:
/showcase - recommended demo script
/rag <question> - route to grounded policy/RAG answer
/tool container <container_no> - route to container tracking
/booking <booking_no> - route to booking status
/ticket <message> - route to support ticket creation
/trace - show last Runtime API metadata
/human <message> - create a pending human approval
/approve <approval_id> - approve a pending approval
/reject <approval_id> - reject a pending approval
/approvals - list pending approvals
/memo remember <key> <value> - remember a thread-scoped memo
/memo get <key> - recall a thread-scoped memo
/memo forget <key> - delete a thread-scoped memo
/memo list - list thread-scoped memos
/skill, /mcp, /a2a, /acp, /deepagent, /eval - future showcases"""

SHOWCASE_RESPONSE = """Recommended demo script:
1. /rag giờ làm việc
2. /tool container ABCD1234567
3. /booking BK123
4. /ticket Tôi cần hỗ trợ
5. /trace
6. /human yêu cầu hoàn phí lưu bãi
7. /memo remember booking BK123
8. /mcp list
9. /a2a ask billing_agent giải thích phí
10. /deepagent lập kế hoạch xử lý khiếu nại"""

PLACEHOLDER_RESPONSES: dict[TelegramCommand, str] = {
    TelegramCommand.SKILL: "Skills showcase is planned for PR-026.",
    TelegramCommand.MCP: "MCP showcase is planned for PR-027.",
    TelegramCommand.A2A: "Agent interop showcase is planned for PR-028.",
    TelegramCommand.ACP: "Agent interop showcase is planned for PR-028.",
    TelegramCommand.DEEPAGENT: "DeepAgents showcase is planned for PR-030.",
    TelegramCommand.EVAL: "Demo eval showcase is planned for PR-029/PR-031.",
}

NO_TRACE_RESPONSE = "No trace metadata is available yet. Invoke a runtime command first."


@dataclass(frozen=True)
class ShowcaseAction:
    """Result of mapping a parsed command for the polling worker."""

    runtime_payload: dict[str, Any] | None = None
    local_response: str | None = None


def map_showcase_command(
    parsed: ParsedTelegramCommand,
    runtime_payload: dict[str, Any],
    *,
    last_trace: dict[str, str] | None = None,
) -> ShowcaseAction:
    """Map a parsed command to either a local response or RuntimeRequest payload."""

    if parsed.command == TelegramCommand.HELP:
        return ShowcaseAction(local_response=HELP_RESPONSE)
    if parsed.command == TelegramCommand.SHOWCASE:
        return ShowcaseAction(local_response=SHOWCASE_RESPONSE)
    if parsed.command == TelegramCommand.TRACE:
        return ShowcaseAction(local_response=format_trace_response(last_trace))
    if parsed.command in PLACEHOLDER_RESPONSES:
        return ShowcaseAction(local_response=PLACEHOLDER_RESPONSES[parsed.command])
    if parsed.command == TelegramCommand.RAG:
        return ShowcaseAction(
            runtime_payload=_with_message(runtime_payload, f"chính sách {parsed.args}")
        )
    if parsed.command == TelegramCommand.TOOL:
        return ShowcaseAction(runtime_payload=_map_tool_command(parsed, runtime_payload))
    if parsed.command == TelegramCommand.BOOKING:
        return ShowcaseAction(
            runtime_payload=_with_message(runtime_payload, f"booking {parsed.args}")
        )
    if parsed.command == TelegramCommand.TICKET:
        return ShowcaseAction(
            runtime_payload=_with_message(runtime_payload, f"ticket {parsed.args}")
        )

    return ShowcaseAction(runtime_payload=runtime_payload)


def format_trace_response(last_trace: dict[str, str] | None) -> str:
    """Return the last known trace metadata for a chat."""

    if not last_trace:
        return NO_TRACE_RESPONSE
    return (
        "Last trace:\n"
        f"request_id={last_trace.get('last_request_id', 'unknown')}\n"
        f"run_id={last_trace.get('last_run_id', 'unknown')}\n"
        f"thread_id={last_trace.get('last_thread_id', 'unknown')}\n"
        f"agent_id={last_trace.get('last_agent_id', 'unknown')}"
    )


def extract_trace_metadata(
    *,
    response: dict[str, Any],
    runtime_payload: dict[str, Any],
    agent_id: str,
) -> dict[str, str]:
    """Extract compact response metadata for later `/trace` output."""

    response_metadata = response.get("metadata")
    metadata = response_metadata if isinstance(response_metadata, dict) else {}
    return {
        "last_request_id": _string_value(metadata.get("request_id")),
        "last_run_id": _string_value(metadata.get("run_id")),
        "last_thread_id": _string_value(runtime_payload.get("thread_id")),
        "last_agent_id": agent_id,
    }


def _map_tool_command(
    parsed: ParsedTelegramCommand,
    runtime_payload: dict[str, Any],
) -> dict[str, Any]:
    """Map `/tool ...` subcommands to deterministic agent-router text."""

    subcommand, _, rest = parsed.args.partition(" ")
    if subcommand.casefold() == "container" and rest.strip():
        return _with_message(runtime_payload, f"tracking container {rest.strip()}")
    return _with_message(runtime_payload, parsed.raw_text)


def _with_message(runtime_payload: dict[str, Any], message: str) -> dict[str, Any]:
    """Return a copied RuntimeRequest payload with a rewritten message."""

    payload = dict(runtime_payload)
    payload["message"] = message.strip()
    metadata = dict(payload.get("metadata") or {})
    metadata["telegram_showcase_original_message"] = runtime_payload.get("message")
    payload["metadata"] = metadata
    return payload


def _string_value(value: Any) -> str:
    """Return a string trace value or `unknown`."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    return "unknown"
