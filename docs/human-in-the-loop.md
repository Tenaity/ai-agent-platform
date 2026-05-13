# Human-In-The-Loop

Human-in-the-loop is a runtime safety and control pattern for pausing high-risk
actions until an operator approves or rejects them. It is separate from prompts,
tool policy, and transport-specific UI.

PR-024 adds a reusable approval contract and local in-memory approval store.
The Telegram worker uses those primitives to showcase `/human`, `/approve`,
`/reject`, and `/approvals` commands without executing real high-risk
production actions.

## Contracts

`snp_agent_core.human_loop` defines:

- `ApprovalStatus`: `pending`, `approved`, `rejected`, `expired`
- `ApprovalRiskLevel`: `low`, `medium`, `high`, `critical`
- `ApprovalRequest`: a domain-neutral Pydantic record for approval state
- `ApprovalStore`: persistence boundary for approval lifecycle operations
- `InMemoryApprovalStore`: local/demo store backed by process memory

Approval records store safe summaries and metadata only. They should not contain
raw secrets or full sensitive payloads.

## Telegram Showcase

The Telegram worker remains a demo UI. It parses commands and composes the
reusable store through `TelegramHumanLoopService`.

Supported local commands:

```text
/human <message>
/approve <approval_id>
/reject <approval_id>
/approvals
```

These commands return local Telegram responses and do not call Runtime API in
PR-024. Normal commands such as `/rag`, `/tool container`, `/booking`, and
`/ticket` continue to route through Runtime API.

## Non-Goals

- No database persistence
- No production API calls
- No real LLM calls
- No webhook or deployment
- No LangGraph interrupt/resume wiring yet

Future PRs can replace `InMemoryApprovalStore` with Postgres or Redis and wire
approval decisions into LangGraph interrupt/resume flows.
