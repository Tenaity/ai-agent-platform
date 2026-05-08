# Tool Execution Interface

PR-012 introduces domain-neutral tool execution contracts and an executor
interface. PR-013 adds `AuditAwareToolExecutor` to wrap any executor and
produce one `ToolCallAuditRecord` per execution.

## Responsibility Split

- `ToolGateway` decides whether an agent may use a tool.
- `ToolExecutor` is the abstract interface for executing a permitted
  capability.
- `PolicyAwareToolExecutor` composes both: it checks policy first, then
  delegates to a wrapped executor only when access is allowed.
- `AuditAwareToolExecutor` wraps any executor (including
  `PolicyAwareToolExecutor`) and produces one `ToolCallAuditRecord` per
  execution attempt, regardless of outcome.

## Contracts

`ToolExecutionRequest` carries:

- tool name
- agent, tenant, user, and channel identity
- input payload
- user scopes
- optional `request_id`, `run_id`, and `thread_id`
- metadata

`ToolExecutionResult` carries:

- tool name
- status: `succeeded`, `failed`, `denied`, `requires_approval`, or `timed_out`
- optional output
- safe error summary
- optional latency
- approval flag
- metadata

## Policy-Aware Execution Flow

```mermaid
flowchart TD
    Request["ToolExecutionRequest"] --> Audit["AuditAwareToolExecutor"]
    Audit --> Wrapper["PolicyAwareToolExecutor"]
    Wrapper --> Gateway["ToolGateway.check_access"]
    Gateway --> Decision{"Decision"}
    Decision -- denied --> Denied["ToolExecutionResult: denied"]
    Decision -- requires_approval --> Approval["ToolExecutionResult: requires_approval"]
    Decision -- allowed --> Executor["ToolExecutor.execute"]
    Executor --> Result["ToolExecutionResult"]
    Executor --> Exception["Executor exception"]
    Exception --> Failed["ToolExecutionResult: failed with safe error"]
    Denied --> AuditRecord["ToolCallAuditRecord written to sink"]
    Approval --> AuditRecord
    Result --> AuditRecord
    Failed --> AuditRecord
```

## Explicit Non-Goals

PR-012 and PR-013 do not add:

- real TMS, CRM, Billing, support, or third-party integrations
- real external API calls
- RAG
- Memory Manager
- Safety pipeline
- real LLM calls
- persistent audit sink (database or log streaming)
- tool execution inside route handlers

Real adapters will come later behind the `ToolExecutor` interface after fake
tool tests and policy enforcement are stable.

See [tool-audit.md](tool-audit.md) for audit record contracts and the
`AuditAwareToolExecutor` composition pattern.
