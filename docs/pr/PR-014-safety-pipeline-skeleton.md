# PR-014: Safety Pipeline Skeleton

## Summary

Introduce a domain-neutral safety pipeline skeleton before real LLM calls, RAG,
memory, production tool integrations, or provider-backed moderation are added.

This PR adds typed safety contracts, a deterministic local policy, a checker
interface, a rule-based checker, and ordered pipeline behavior. It also adds a
permissive input precheck in `InvocationService` so safety is represented as a
runtime boundary while preserving existing runtime and eval behavior.

## Scope

- Add `packages/snp_agent_safety` contracts:
  - `SafetyStage`
  - `SafetyDecision`
  - `SafetySeverity`
  - `SafetyCheckRequest`
  - `SafetyCheckResult`
- Add deterministic policy and checker primitives:
  - `SafetyPolicy`
  - `SafetyChecker`
  - `RuleBasedSafetyChecker`
  - `SafetyPipeline`
- Add focused unit tests for contracts, rule behavior, pipeline stop behavior,
  redaction, case-insensitive matching, and no network dependency.
- Add runtime service tests for permissive safe input and blocked input
  returning `rejected_by_safety` with lifecycle metadata.
- Add safety docs and update architecture / agent development documentation.

## Non-Goals

- No real moderation API calls.
- No real LLM calls or LLM judge.
- No RAG.
- No Memory Manager.
- No real TMS, CRM, Billing, support, or other production integrations.
- No database persistence.
- No route handler business logic.

## Design Notes

Safety is not just a prompt. It is a runtime boundary with typed inputs and
typed decisions.

The safety pipeline is separate from Tool Gateway policy:

- Tool Gateway governs whether an agent may access a registered tool.
- Safety Pipeline governs whether content may proceed, be blocked, require
  human review, or be redacted.

`RuleBasedSafetyChecker` is deliberately simple and deterministic. It matches
blocked and human review terms case-insensitively, can redact simple
email-like and phone-like patterns, and avoids including raw sensitive details
in reasons.

Future PRs can add prompt-injection detection, jailbreak detection, document
safety, richer PII policy, tenant-specific policy loading, output safety,
tool-stage safety, and provider-backed moderation by implementing
`SafetyChecker`.

## Acceptance Criteria

- `make lint` passes.
- `make typecheck` passes.
- `make test` passes.
- `make eval` passes.
