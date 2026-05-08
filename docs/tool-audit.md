# Tool Call Audit

PR-013 introduces domain-neutral tool call audit contracts and an in-memory
audit sink. The audit layer is separate from LangSmith tracing and provides
security, operations, and compliance records for every tool call attempt.

## What Audit Records Are

A `ToolCallAuditRecord` captures:

- **Who** called the tool — agent, tenant, user, channel identity.
- **What** was called — tool name and status.
- **When** it happened — UTC-aware timestamp.
- **What the outcome was** — succeeded, failed, denied, requires_approval, timed_out.
- **Correlation identifiers** — request_id, run_id, and thread_id when available.
- **Safe summaries** — input and output field **key names only**, never raw values.
- **Safe error message** — a human-readable error summary, never a stack trace.

## What Audit Records Are NOT

Audit records are **not** LangSmith traces.

| | Audit Records | LangSmith Traces |
|---|---|---|
| Owner | `snp_agent_tools` audit layer | `snp_agent_observability` tracing layer |
| Purpose | Security, ops, compliance | Model debugging, token usage, latency |
| Content | Identity, status, outcome | Full input/output, model reasoning |
| Persistence | Future: durable sink | LangSmith SaaS |
| Raw payloads | Never | Yes, with appropriate data controls |

## ToolCallAuditStatus Values

| Status | Meaning |
|---|---|
| `allowed` | Policy approved the call (before execution) |
| `denied` | Policy denied the call (never executed) |
| `requires_approval` | Policy requires human approval (paused) |
| `succeeded` | Tool executed and returned a result |
| `failed` | Tool executed but returned an error or raised |
| `timed_out` | Tool execution exceeded the time budget |

`AuditAwareToolExecutor` maps `ToolExecutionStatus` → `ToolCallAuditStatus`
automatically after wrapping a policy-aware or plain executor.

## Why Raw Input/Output Is Not Stored

Tool inputs often contain customer identifiers, booking references, and
descriptions that may include PII or sensitive business data. Storing raw
payloads in audit records would:

- Risk exposing PII in audit logs.
- Violate data minimization principles.
- Create large, expensive-to-manage audit records.

Instead, `AuditAwareToolExecutor` stores only the top-level key **names**
of the input and output dictionaries:

```
input_summary:  "container_id"
output_summary: "container_id, last_event, status"
```

Raw values are never stored. A future forensic integration may reconstruct
payloads from trace storage with appropriate access controls.

## Composition Pattern

`AuditAwareToolExecutor` wraps any `ToolExecutor`, including
`PolicyAwareToolExecutor`. The recommended composition order is:

```
AuditAwareToolExecutor
  └── PolicyAwareToolExecutor
        └── ConcreteToolExecutor (fake or real)
```

This means the audit record reflects the **final** result after policy has
already been applied — including denied and requires_approval outcomes:

```python
from snp_agent_tools import (
    AuditAwareToolExecutor,
    InMemoryToolCallAuditSink,
    PolicyAwareToolExecutor,
)

fake = CustomerServiceFakeToolExecutor()
policy_executor = PolicyAwareToolExecutor(gateway=gateway, executor=fake)
sink = InMemoryToolCallAuditSink()

executor = AuditAwareToolExecutor(executor=policy_executor, audit_sink=sink)

result = executor.execute(request)
records = sink.list_records()  # one record per execution
```

## In-Memory Audit Sink

`InMemoryToolCallAuditSink` is provided for unit tests and local development:

- Stores records in a list in insertion order.
- Not thread-safe.
- Does not persist across process restarts.
- **Do not use in production.**

```python
from snp_agent_tools import InMemoryToolCallAuditSink

sink = InMemoryToolCallAuditSink()
sink.record(record)
all_records = sink.list_records()
```

## Future: Persistent Audit Sink

A persistent `ToolCallAuditSink` backed by a database or log streaming
service will be added in a later PR. The `ToolCallAuditSink` abstract base
class is stable; implementing a new sink requires only two methods:

```python
class MyPersistentSink(ToolCallAuditSink):
    def record(self, record: ToolCallAuditRecord) -> None: ...
    def list_records(self) -> list[ToolCallAuditRecord]: ...
```

## Explicitly Not Added in PR-013

- Persistent audit sink (database or log streaming)
- Async audit sink
- Audit filtering, querying, or aggregation
- Real TMS, CRM, Billing, or support integrations
- RAG, Memory Manager, Safety pipeline
- Real LLM calls
- Database persistence
- Route handler tool execution

See [tool-execution.md](tool-execution.md) for the execution interface.
See [tool-gateway.md](tool-gateway.md) for the policy decision layer.
