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
