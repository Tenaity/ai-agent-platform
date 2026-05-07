# Evaluation Playbook

Regression evaluation is a release gate for agent behavior. Every material
behavior change should add or update scenarios that capture the expected
outcome, failure mode, and safety boundary.

Future eval suites should cover:

- Happy-path task completion.
- Known regressions and previously reported defects.
- Tool-denied and tool-unavailable flows.
- Retrieval misses and conflicting context.
- Safety escalations and human-review paths.

PR-001 only establishes the documentation and manifest fields required for
future eval wiring.
