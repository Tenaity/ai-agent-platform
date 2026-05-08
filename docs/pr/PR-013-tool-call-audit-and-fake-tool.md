# PR-013 Tool Call Audit Record + Fake Customer Service Tool

## Summary

- Add `ToolCallAuditStatus` enum and `ToolCallAuditRecord` Pydantic model as
  domain-neutral security and operations audit contracts.
- Add `ToolCallAuditSink` abstract base class and `InMemoryToolCallAuditSink`
  for test and local-dev use.
- Add `AuditAwareToolExecutor` wrapper that produces exactly one
  `ToolCallAuditRecord` per tool execution attempt, regardless of outcome.
- Make `PolicyAwareToolExecutor` inherit from `ToolExecutor` so it can be
  composed with `AuditAwareToolExecutor` without an adapter shim.
- Add `CustomerServiceFakeToolExecutor` under `agents/customer_service/` with
  deterministic, side-effect-free responses for the three sample customer
  service tools.
- Add comprehensive tests covering validation, sink behavior, executor
  wrapping, no-trace-leak guarantees, ID propagation, fake tool outputs, and
  the full composition stack.
- Add `docs/tool-audit.md` and update `docs/tool-execution.md`,
  `docs/tool-gateway.md`, `docs/tools.md`, and
  `docs/architecture/overview.md`.

## Scope

- `packages/snp_agent_tools/src/snp_agent_tools/audit.py` — NEW
- `packages/snp_agent_tools/src/snp_agent_tools/audit_sink.py` — NEW
- `packages/snp_agent_tools/src/snp_agent_tools/audit_executor.py` — NEW
- `packages/snp_agent_tools/src/snp_agent_tools/policy_executor.py` — MODIFY
  (add `ToolExecutor` as base class)
- `packages/snp_agent_tools/src/snp_agent_tools/__init__.py` — MODIFY
  (export new audit symbols)
- `agents/customer_service/fake_tools.py` — NEW
- `tests/test_tool_audit.py` — NEW
- `docs/tool-audit.md` — NEW
- `docs/tool-execution.md` — UPDATE
- `docs/tool-gateway.md` — UPDATE
- `docs/tools.md` — UPDATE
- `docs/architecture/overview.md` — UPDATE
- `docs/pr/PR-013-tool-call-audit-and-fake-tool.md` — NEW

## Explicitly Not Added

- Real TMS, CRM, Billing, support, or third-party integrations
- Real external API calls
- RAG
- Memory Manager
- Safety pipeline
- Real LLM calls
- Persistent audit sink (database or log streaming)
- Route handler tool execution

## Architecture Notes

### Audit vs. LangSmith Trace

`ToolCallAuditRecord` is a **security and operations record**. It is not a
LangSmith trace. The distinction:

| | Audit Record | LangSmith Trace |
|---|---|---|
| Owner | `snp_agent_tools` | `snp_agent_observability` |
| Purpose | Security, compliance, incident response | Model debugging, token usage |
| Raw payloads | Never stored | Yes (with data controls) |
| Storage | Future persistent sink | LangSmith SaaS |

### Why Raw Inputs/Outputs Are Not Stored

Tool inputs may contain customer identifiers, booking references, and
descriptions. Storing raw values in audit logs risks PII leakage and violates
data minimization principles. `AuditAwareToolExecutor` stores only the
**top-level key names** of input and output dictionaries:

```
input_summary:  "container_id"
output_summary: "container_id, last_event, status"
```

### Composition Order

The recommended stack is:

```
AuditAwareToolExecutor        ← observes final result, writes audit record
  └── PolicyAwareToolExecutor ← applies policy, may deny or gate
        └── ConcreteExecutor  ← fake or real tool adapter
```

The audit layer sits **outside** the policy layer so that denied and
requires_approval outcomes are also audited.

### In-Memory Sink is Test/Local Only

`InMemoryToolCallAuditSink` is not thread-safe and does not persist across
process restarts. It is suitable for unit tests and local debugging only. A
persistent sink will be added in a later PR when the audit record contract is
stable and deployment requirements are understood.

### Fake Tool Executor is Domain-Specific

`CustomerServiceFakeToolExecutor` lives under `agents/customer_service/` rather
than `packages/snp_agent_tools/` because it is domain-specific. The
domain-neutral `ToolExecutor` interface it implements belongs to the platform
package. This import direction (agent → package) is explicitly allowed by the
architecture rules.

## Tests

- `ToolCallAuditRecord` validates required fields
- Blank identity fields raise `ValidationError`
- Naive `created_at` raises `ValidationError`
- `created_at` is stored as UTC-aware
- Optional fields default to `None`
- `extra="forbid"` rejects unknown fields
- `InMemoryToolCallAuditSink` starts empty
- `InMemoryToolCallAuditSink` preserves insertion order
- `InMemoryToolCallAuditSink.list_records()` returns a snapshot
- `AuditAwareToolExecutor` creates succeeded audit on success
- `AuditAwareToolExecutor` stores output key names only (not raw values)
- `AuditAwareToolExecutor` stores input key names only (not raw values)
- `AuditAwareToolExecutor` creates failed audit when executor raises
- `AuditAwareToolExecutor` does not leak Traceback/stack traces
- `request_id`, `run_id`, `thread_id` propagated into audit record
- Absent correlation IDs stored as None
- Fake executor: `tracking_container` known ID → deterministic output
- Fake executor: `tracking_container` unknown ID → UNKNOWN status
- Fake executor: `check_booking_status` known ID → deterministic output
- Fake executor: `check_booking_status` unknown ID → UNKNOWN status
- Fake executor: `create_support_ticket` → deterministic ticket ID
- Fake executor: unknown tool → safe `failed` result
- Composition: allowed tool → succeeded result + succeeded audit
- Composition: denied tool → denied result + denied audit
- Composition: requires_approval tool → requires_approval result + audit

## Risk

- Low. This PR adds contracts, wrappers, a fake executor, and tests only.
- `PolicyAwareToolExecutor` now inherits from `ToolExecutor` — this is additive
  and backward-compatible; all existing call sites remain valid.
- No external calls, credentials, persistence, or route handler changes.

## Follow-up PRs

- Persistent `ToolCallAuditSink` (database or log streaming).
- Real customer-service tool adapters behind the fake interface.
- Safety pipeline skeleton.
- RAG contracts.
