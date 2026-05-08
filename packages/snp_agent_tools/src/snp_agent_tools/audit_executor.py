"""Audit-aware executor wrapper for tool call observability.

``AuditAwareToolExecutor`` wraps any ``ToolExecutor`` (including
``PolicyAwareToolExecutor``) and produces exactly one ``ToolCallAuditRecord``
per execution attempt. The record is written to a ``ToolCallAuditSink``
regardless of whether execution succeeds, fails, or is denied by policy.

Composition example — audit wraps the policy-aware executor so the audit record
reflects the final result after policy has already been applied::

    from snp_agent_tools import (
        AuditAwareToolExecutor,
        InMemoryToolCallAuditSink,
        PolicyAwareToolExecutor,
    )

    inner_executor = MyConcreteToolExecutor()
    policy_executor = PolicyAwareToolExecutor(gateway=gateway, executor=inner_executor)
    audit_sink = InMemoryToolCallAuditSink()
    executor = AuditAwareToolExecutor(executor=policy_executor, audit_sink=audit_sink)

    result = executor.execute(request)
    records = audit_sink.list_records()

Security constraints:
- ``error_summary`` must never contain stack traces, exception class names, or
  implementation-specific details that could aid an attacker.
- ``input_summary`` and ``output_summary`` contain key names only, no raw values.
- Unexpected exceptions from the wrapped executor are caught, returned as safe
  failed results, and recorded — the exception is never re-raised.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from snp_agent_tools.audit import ToolCallAuditRecord, ToolCallAuditStatus
from snp_agent_tools.audit_sink import ToolCallAuditSink
from snp_agent_tools.execution import (
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus,
)
from snp_agent_tools.executor import ToolExecutor

# Map from execution status to the corresponding audit status.
# ALLOWED is not a ToolExecutionStatus, so it has no mapping here.
_STATUS_MAP: dict[ToolExecutionStatus, ToolCallAuditStatus] = {
    ToolExecutionStatus.SUCCEEDED: ToolCallAuditStatus.SUCCEEDED,
    ToolExecutionStatus.FAILED: ToolCallAuditStatus.FAILED,
    ToolExecutionStatus.DENIED: ToolCallAuditStatus.DENIED,
    ToolExecutionStatus.REQUIRES_APPROVAL: ToolCallAuditStatus.REQUIRES_APPROVAL,
    ToolExecutionStatus.TIMED_OUT: ToolCallAuditStatus.TIMED_OUT,
}


def _summarize_keys(payload: dict[str, Any] | None) -> str | None:
    """Return a comma-separated list of top-level key names, or None.

    Summaries never include raw values to prevent PII or sensitive business
    data from being stored in audit records.
    """

    if payload is None:
        return None
    keys = sorted(payload.keys())
    return ", ".join(keys) if keys else None


class AuditAwareToolExecutor(ToolExecutor):
    """Executor wrapper that produces one audit record per tool call.

    This wrapper composes with any ``ToolExecutor``, including
    ``PolicyAwareToolExecutor``, by wrapping it and observing the result.
    It does not make policy decisions itself — it only records what happened.

    The audit record captures:
    - identity context from the execution request
    - the final execution status mapped to ``ToolCallAuditStatus``
    - correlation identifiers (request_id, run_id, thread_id) when present
    - latency reported by the wrapped executor when present
    - a summary of input and output field names (no raw values)
    - a safe error summary when execution fails (no stack traces)

    If the wrapped executor raises an unexpected exception, this wrapper:
    1. Returns a safe ``failed`` ``ToolExecutionResult`` to the caller.
    2. Records a ``failed`` audit record with a generic error summary.
    3. Does not re-raise the exception.
    """

    def __init__(self, executor: ToolExecutor, audit_sink: ToolCallAuditSink) -> None:
        """Create an audit-aware wrapper around the given executor.

        Args:
            executor: The concrete or wrapped executor to delegate to. May be
                a ``PolicyAwareToolExecutor`` adapter or any other ``ToolExecutor``.
            audit_sink: The sink that receives one audit record per execution.
        """

        self._executor = executor
        self._audit_sink = audit_sink

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute the request via the wrapped executor and record an audit entry.

        The audit record is written to the sink before this method returns,
        regardless of whether execution succeeded or failed.
        """

        result: ToolExecutionResult
        try:
            result = self._executor.execute(request)
        except Exception:
            # Unexpected exceptions from the wrapped executor are caught here so
            # callers receive a safe result and the audit log captures the failure.
            result = ToolExecutionResult(
                tool_name=request.tool_name,
                status=ToolExecutionStatus.FAILED,
                error="Tool execution failed unexpectedly.",
            )

        audit_status = _STATUS_MAP.get(result.status, ToolCallAuditStatus.FAILED)

        # Build a safe error summary — never include stack traces or exception
        # types, only a sanitized message from the result.
        error_summary: str | None = None
        if result.error:
            error_summary = result.error[:500]  # Cap length for audit safety.

        audit_record = ToolCallAuditRecord(
            audit_id=str(uuid.uuid4()),
            tool_name=request.tool_name,
            agent_id=request.agent_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            channel=request.channel,
            status=audit_status,
            request_id=request.request_id,
            run_id=request.run_id,
            thread_id=request.thread_id,
            latency_ms=result.latency_ms,
            input_summary=_summarize_keys(request.input),
            output_summary=_summarize_keys(result.output),
            error_summary=error_summary,
            created_at=datetime.now(UTC),
        )

        self._audit_sink.record(audit_record)

        return result
