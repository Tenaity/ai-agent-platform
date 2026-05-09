# Safety Pipeline

PR-014 introduces a domain-neutral safety pipeline skeleton. It is a runtime
boundary for checking content before or around agent execution, not a prompt
instruction and not a production moderation integration.

## What Exists

- `SafetyCheckRequest`: typed input for a safety check, including stage,
  runtime identity, content, and metadata.
- `SafetyCheckResult`: typed decision with severity, safe reason, optional
  redacted content, flags, and metadata.
- `SafetyPolicy`: deterministic local policy with blocked terms, human review
  terms, optional simple PII redaction, and a default decision.
- `SafetyChecker`: abstract checker interface.
- `RuleBasedSafetyChecker`: local deterministic implementation.
- `SafetyPipeline`: ordered checker pipeline that stops on blocked, human
  review, or redacted decisions.

The Runtime API uses a permissive default safety pipeline before graph
execution. With the default policy, existing graph execution and eval behavior
are unchanged. If an injected policy blocks input, `InvocationService` returns a
`RuntimeResponse` with `status=rejected_by_safety` and lifecycle metadata.

## Safety Stages

Safety checks are labeled by stage:

- `input`: user or caller content before graph execution.
- `tool`: future tool request or tool result safety checks.
- `output`: final or intermediate agent output before external use.

The current runtime wiring applies only an input precheck.

## Deterministic Only

This PR does not add:

- external moderation API calls
- real LLM calls
- LLM-as-judge safety decisions
- RAG or document safety scanning
- memory safety policy
- database persistence
- production tool, CRM, TMS, Billing, or support integrations

The rule-based checker is intentionally simple and local. It uses
case-insensitive term matching and basic email-like / phone-like redaction
patterns when redaction is enabled.

## Relationship To Tool Policy

The safety pipeline is separate from Tool Gateway policy.

Tool Gateway answers whether an agent may access a registered tool under a
policy. Safety answers whether content should proceed, be blocked, require
human review, or be redacted. Future tool-stage safety checks may run before or
after Tool Gateway decisions, but the contracts remain separate.

## Future Extensions

Future PRs can add:

- prompt-injection detection
- jailbreak detection
- document and attachment safety
- richer PII policy
- tenant-specific policy loading
- provider-backed moderation adapters
- output safety checks
- tool input and tool result safety checks

Provider-backed checks should implement `SafetyChecker` and keep route handlers
thin. Apps must not own reusable safety logic, and no checker should leak raw
sensitive details in user-facing reasons or audit summaries.
