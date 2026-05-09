# Scaffold Templates

PR-016 turns the repository into a reusable AI Agent Platform scaffold. The
templates are project starting points aligned to the platform contracts; they
are not runtime code and should not be imported by packages.

## Philosophy

Templates exist so new agent projects start with the same boundaries as the
framework:

- typed manifests
- typed graph state
- runtime-compatible graph entrypoints
- explicit safety, retrieval, and tool boundaries
- regression eval placeholders
- no production secrets
- no hidden production behavior in prompts

The intended flow is:

```text
template -> generated agent -> tests -> eval -> runtime deployment
```

The local generator CLI automates the copy/substitution step:

```bash
PYTHONPATH=apps/agent-cli/src uv run python -m agent_cli.main create-agent \
  --template agent-basic \
  --name my_agent \
  --domain my_domain \
  --output-dir agents
```

Use `--dry-run` to preview the files that would be created. Generated projects
still need review, tests, regression datasets, evals, and normal runtime
registration decisions.

## Template Types

| Template | Use when | Excludes |
|---|---|---|
| `agent-basic` | You need a minimal deterministic LangGraph workflow. | RAG, tools, production integrations. |
| `agent-rag` | You need document QA shape with retrieval contracts and citations. | Vector DBs, ingestion, real LLM calls. |
| `agent-tool` | You need action-oriented tool structure with policy and audit shape. | Real external APIs. |
| `agent-full-demo` | You need a reference project shape combining safety, RAG, tools, and evals. | Production adapters and persistence. |

## Templates Vs Examples

Templates are reusable scaffolds. They contain placeholders and should stay
domain-neutral where possible.

Examples are reference implementations or project notes. They can describe a
concrete scenario, such as `examples/current_chatbot_demo`, but they must not be
imported by framework packages and must not become production integration code.

## Maintenance Rules

- New agent/project patterns should be reflected in templates.
- Templates must remain aligned with platform contracts.
- Templates must not contain production secrets.
- Templates should not add runtime behavior by themselves.
- Examples must not be imported by packages.
- Generator behavior should stay deterministic and avoid external services.
