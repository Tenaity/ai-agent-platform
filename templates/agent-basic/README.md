# Agent Basic Template

Use this template for a minimal LangGraph agent with no RAG, no tools, and no
production integrations. It is intended for simple workflow experiments and
contract-first agent scaffolding.

## Files

- `agent.yaml.template`: manifest shape for a domain-specific agent.
- `graph.py.template`: deterministic graph runner skeleton.
- `state.py.template`: typed graph state placeholder.
- `prompts/system.md.template`: starter system prompt.
- `evals/eval.yaml.template`: regression eval config placeholder.

Replace `{{agent_id}}`, `{{agent_module}}`, `{{owner}}`, and related placeholders
when copying this template into `agents/<agent_id>/`.
