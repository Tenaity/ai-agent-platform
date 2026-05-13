"""Telegram-facing human-in-the-loop showcase service.

The reusable approval contracts and store live in `snp_agent_core`. This module
only adapts Telegram commands into local demo responses.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from snp_agent_core.human_loop import (
    ApprovalNotFoundError,
    ApprovalRequest,
    ApprovalRiskLevel,
    ApprovalStateError,
    ApprovalStore,
    InMemoryApprovalStore,
)
from telegram_worker.commands import ParsedTelegramCommand, TelegramCommand


class TelegramHumanLoopService:
    """Local Telegram demo service for approval commands."""

    def __init__(self, store: ApprovalStore | None = None) -> None:
        """Create a service backed by the provided approval store."""

        self._store = store or InMemoryApprovalStore()

    def handle(
        self,
        parsed: ParsedTelegramCommand,
        *,
        runtime_payload: dict[str, Any],
        agent_id: str,
    ) -> str | None:
        """Return a local response for HITL commands, or `None` if not handled."""

        if parsed.command == TelegramCommand.HUMAN:
            return self._create(parsed, runtime_payload=runtime_payload, agent_id=agent_id)
        if parsed.command == TelegramCommand.APPROVE:
            return self._approve(parsed, runtime_payload=runtime_payload)
        if parsed.command == TelegramCommand.REJECT:
            return self._reject(parsed, runtime_payload=runtime_payload)
        if parsed.command == TelegramCommand.APPROVALS:
            return self._list_pending()
        return None

    def _create(
        self,
        parsed: ParsedTelegramCommand,
        *,
        runtime_payload: dict[str, Any],
        agent_id: str,
    ) -> str:
        summary = parsed.args.strip()
        if not summary:
            return "Usage: /human <message>"

        approval = ApprovalRequest(
            approval_id=f"approval-{uuid4().hex[:12]}",
            agent_id=agent_id,
            tenant_id=str(runtime_payload["tenant_id"]),
            user_id=str(runtime_payload["user_id"]),
            channel=str(runtime_payload["channel"]),
            thread_id=_optional_string(runtime_payload.get("thread_id")),
            request_id=_optional_string(runtime_payload.get("request_id")),
            run_id=_optional_string(runtime_payload.get("run_id")),
            action_name="telegram_showcase_human_review",
            action_summary=summary,
            risk_level=ApprovalRiskLevel.HIGH,
            created_at=datetime.now(UTC),
            metadata=_safe_telegram_metadata(runtime_payload),
        )
        self._store.create(approval)
        return (
            "Approval request created:\n"
            f"approval_id={approval.approval_id}\n"
            f"status={approval.status.value}\n"
            f"risk_level={approval.risk_level.value}\n"
            f"action={approval.action_summary}\n"
            f"Use /approve {approval.approval_id} or /reject {approval.approval_id}."
        )

    def _approve(
        self,
        parsed: ParsedTelegramCommand,
        *,
        runtime_payload: dict[str, Any],
    ) -> str:
        approval_id = parsed.args.strip()
        if not approval_id:
            return "Usage: /approve <approval_id>"
        try:
            approval = self._store.approve(
                approval_id,
                decided_by=str(runtime_payload["user_id"]),
                reason="Approved from Telegram showcase.",
            )
        except (ApprovalNotFoundError, ApprovalStateError) as exc:
            return str(exc)
        return (
            "Approval approved: "
            f"approval_id={approval.approval_id} status={approval.status.value}"
        )

    def _reject(
        self,
        parsed: ParsedTelegramCommand,
        *,
        runtime_payload: dict[str, Any],
    ) -> str:
        approval_id = parsed.args.strip()
        if not approval_id:
            return "Usage: /reject <approval_id>"
        try:
            approval = self._store.reject(
                approval_id,
                decided_by=str(runtime_payload["user_id"]),
                reason="Rejected from Telegram showcase.",
            )
        except (ApprovalNotFoundError, ApprovalStateError) as exc:
            return str(exc)
        return (
            "Approval rejected: "
            f"approval_id={approval.approval_id} status={approval.status.value}"
        )

    def _list_pending(self) -> str:
        pending = self._store.list_pending()
        if not pending:
            return "No pending approvals."
        lines = ["Pending approvals:"]
        lines.extend(
            f"- {approval.approval_id} risk={approval.risk_level.value} "
            f"action={approval.action_summary}"
            for approval in pending
        )
        return "\n".join(lines)


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


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
