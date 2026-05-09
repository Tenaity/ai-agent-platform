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

4. Keep `templates/` as scaffolds.
   - New agent/project patterns should be reflected in templates.
   - Templates must not contain production secrets.
   - Templates are not runtime code.

5. Keep `examples/` as reference implementations.
   - Examples may document concrete project wiring.
   - Examples must not be imported by packages.
   - Examples must not hide production integrations.

6. Every agent workflow must be:
   - modular
   - traceable
   - evaluable
   - memory-aware
   - tool-governed
   - safety-bounded
   - reusable across domains where possible

7. Do not hard-code secrets.
   - Use environment variables.
   - Update `.env.example` whenever new configuration is introduced.

8. Prefer explicit contracts over implicit dictionaries.
   - Use Pydantic models for public configuration and runtime contracts.
   - Use typed state schemas for graph state.
   - Validate external inputs at boundaries.

9. Comments and docstrings should explain intent.
   - Explain invariants, extension points, and non-obvious design decisions.
   - Do not add comments that merely restate obvious code.

10. Testing is mandatory.
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

## Git Process

- Use PR-numbered branch names: `pr-00N-short-kebab-summary`.
  - Examples: `pr-006-regression-eval-skeleton`, `pr-007-runtime-execution-lifecycle`.
  - Do not add tool-specific prefixes such as `codex/` unless the user explicitly asks for them.
- Use concise commit subjects that preserve the PR number for primary feature work.
  - Preferred format: `<type>(<scope>): PR-00N <short summary>`.
  - Examples: `feat(eval): PR-006 regression evaluation skeleton`, `feat(runtime): PR-007 runtime execution lifecycle`.
  - Small follow-up commits may omit the PR number when the subject is clearer without it, for example `test: cover graph execution failure response`.
- Keep commit messages specific to the change. Mention the platform area (`runtime`, `eval`, `graph`, `docs`, etc.) when it improves reviewability.
- For every PR, create or update `docs/pr/PR-XXX-*.md` with a GitHub-ready PR description.
- Before pushing, run the PR acceptance checks from the user request. If a Makefile target cannot run because local tooling is missing, run the equivalent project environment command and report the blocker clearly.

## Forbidden Patterns

- No direct LLM calls inside API route handlers.
- No direct tool calls from agent nodes without a Tool Gateway.
- No unvalidated dictionaries crossing package boundaries.
- No production behavior hidden only in prompts.
- No global mutable state for runtime/session data.
- No secret values committed to the repository.
