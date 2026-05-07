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
