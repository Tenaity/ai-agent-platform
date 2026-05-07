# ADR 0001: Use a Monorepo Platform Architecture

## Status

Accepted.

## Context

The platform must support reusable SDK packages, thin runtime apps, and
domain-specific agents that evolve together. Early development will change
contracts across these boundaries frequently.

## Decision

Start with a Python monorepo containing `apps/`, `packages/`, `agents/`,
`prompts/`, `datasets/`, `docs/`, and `infra/`.

## Consequences

- Shared contracts can be reviewed and tested with the apps that consume them.
- Agent manifests and regression tests can live near platform contract changes.
- Cross-package coupling remains visible during code review.
- Future extraction into separate repositories remains possible after the
  boundaries stabilize.
