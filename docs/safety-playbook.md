# Safety Playbook

Safety boundaries must be explicit, testable, and enforced outside prompt text
wherever possible.

Future safety controls should include:

- Manifest-declared safety profiles.
- Input and output validation at runtime boundaries.
- Tool policies enforced by the Tool Gateway.
- Human-review routing for high-impact responses.
- Regression tests for refusals, escalations, and sensitive workflows.

No PR should introduce direct LLM calls, direct tool calls, or secret handling
that bypasses these boundaries.
