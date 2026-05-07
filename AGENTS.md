# AGENTS.md

## Repository Mission

This repository implements `snp-ai-agent-platform`: an internal AI Agent Platform SDK + Runtime for building modular, traceable, evaluable, memory-aware, tool-governed, safety-bounded, reusable agent workflows across domains.

This is a platform/framework repository, not a one-off chatbot implementation.

## Architectural Rules

1. Keep `apps/` thin.
   - Apps expose APIs, CLIs, or workers.
   - Apps should not contain reusable domain-neutral platform logic.

2. Keep `packages/` reusable.
   - Platform primitives live in packages.
   - Packages should avoid importing from apps.
   - Cross-package dependencies must remain intentional and documented.

3. Keep `agents/` domain-specific.
   - Each agent must have an `agent.yaml`.
   - Each agent should eventually define graph, prompts, tools, evals, and tests.
   - Agent behavior must be versioned and testable.

4. Every agent workflow must be:
   - modular
   - traceable
   - evaluable
   - memory-aware
   - tool-governed
   - safety-bounded
   - reusable across domains where possible

5. Do not hard-code secrets.
   - Use environment variables.
   - Update `.env.example` whenever new configuration is introduced.

6. Prefer explicit contracts over implicit dictionaries.
   - Use Pydantic models for public configuration and runtime contracts.
   - Use typed state schemas for graph state.
   - Validate external inputs at boundaries.

7. Comments and docstrings should explain intent.
   - Explain invariants, extension points, and non-obvious design decisions.
   - Do not add comments that merely restate obvious code.

8. Testing is mandatory.
   - Public contracts require unit tests.
   - Agent behavior requires regression tests.
   - Tool execution requires fake-tool integration tests before real integrations.

## Code Style

- Python 3.11+.
- Use type hints.
- Use Pydantic for config and API contracts.
- Use ruff for linting and formatting.
- Use mypy for type checking.
- Use pytest for tests.

## PR Discipline

Each PR should be small and reviewable.

A good PR has:
- clear purpose
- clear acceptance criteria
- tests
- documentation updates
- no unrelated refactors

## Forbidden Patterns

- No direct LLM calls inside API route handlers.
- No direct tool calls from agent nodes without a Tool Gateway.
- No unvalidated dictionaries crossing package boundaries.
- No production behavior hidden only in prompts.
- No global mutable state for runtime/session data.
- No secret values committed to the repository.