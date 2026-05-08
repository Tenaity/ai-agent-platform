# Agent Development Guide

Each agent lives under `agents/<agent_id>/` and must include an `agent.yaml`
manifest. The manifest is the public contract between domain-specific behavior
and the reusable platform runtime.

Future agent packages should include:

- A typed manifest with owner, version, runtime, model policy, tools, safety,
  observability, and eval sections.
- Graph construction code behind a stable entrypoint.
- Prompt assets that are versioned with behavior changes.
- Fake-tool integration tests before real tool integrations.
- Regression evals for known user journeys and safety-sensitive cases.

Agents must not hide production behavior only in prompts. Workflow state,
external inputs, and tool results should cross package boundaries through typed
contracts.

## Graph Contract

LangGraph agents declare their graph entrypoint in `agent.yaml`:

```yaml
runtime:
  type: langgraph
  graph: agents.customer_service.graph:build_graph
  state_schema: agents.customer_service.state:CustomerServiceState
```

`build_graph()` accepts the optional runtime-provided `checkpointer` argument
and returns an object with an `invoke()` method, typically a compiled LangGraph
`StateGraph`. The state schema should be a typed state object, such as a
`TypedDict`, with fields needed by the runtime adapter and graph nodes.

The current sample graph remains deterministic and local. Do not add real LLM
provider calls, real tools, persistence, RAG, or production integrations until
the platform contracts for those concerns exist.

## Tool Specs

Agents may declare domain-specific sample tool specs in code, but PR-009 specs
are capability metadata only. A `ToolSpec` describes what a tool can do, what
schemas it accepts and returns, which scopes it requires, and what risk or
approval posture it has.

Sample customer service specs live in `agents/customer_service/tools.py`.
They do not include execution functions and must not call real TMS, CRM,
Billing, support, or other third-party systems.

Reusable contracts and registry behavior live in `snp_agent_tools`:

- `ToolSpec`
- `ToolRiskLevel`
- `ToolExecutionMode`
- `ToolRegistry`

The future Tool Gateway will be responsible for validation, policy enforcement,
approval checks, audit records, and execution routing. Agent code should not
call tools directly.

PR-010 adds the first policy-only gateway skeleton. Agents may be checked
against `ToolPolicy` through `ToolGateway.check_access()`, but this still does
not execute tools. Any code that needs a tool decision should consume the
gateway result and wait for a later execution adapter PR before invoking real or
fake integrations.

See [tools.md](tools.md) and [tool-gateway.md](tool-gateway.md) for the current
tool contracts and policy skeleton.

## Runtime Contract Examples

Runtime adapters receive a `RuntimeRequest` after the platform has selected an
agent and validated routing context:

```json
{
  "tenant_id": "tenant_demo",
  "channel": "api",
  "user_id": "user_123",
  "thread_id": "thread_456",
  "message": "How do I reset my password?",
  "metadata": {
    "locale": "en-US"
  }
}
```

Runtime adapters return a `RuntimeResponse`. The response is a boundary object,
not a LangGraph implementation detail:

```json
{
  "thread_id": "thread_456",
  "status": "completed",
  "answer": "Use the password reset link in your account settings.",
  "citations": [
    {
      "source_id": "kb-password-reset",
      "title": "Password reset guide",
      "uri": "https://example.invalid/kb/password-reset",
      "quote": "Open account settings and choose reset password.",
      "metadata": {}
    }
  ],
  "tool_calls": [
    {
      "tool": "knowledge_base.search",
      "status": "completed",
      "latency_ms": 42,
      "input_summary": "password reset query",
      "output_summary": "one relevant article",
      "error": null
    }
  ],
  "trace_id": "trace_789",
  "handoff_required": false,
  "metadata": {
    "agent_id": "customer_service"
  }
}
```
