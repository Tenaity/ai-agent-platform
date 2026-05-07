# Evaluation Playbook

Regression evaluation is a release gate for agent behavior. Every material
behavior change should add or update scenarios that capture the expected
outcome, failure mode, and safety boundary.

---

## Local Regression Flow (PR-006)

The local eval runner runs agent graphs **in-process** — no real LLM calls,
no LangSmith credentials, no external APIs. It is suitable for pre-commit
checks, CI gating, and iterative development.

### Quick Start

```bash
make eval AGENT=snp.customer_service.zalo DATASET=datasets/customer_service/regression_v1.jsonl
```

Or invoke directly:

```bash
uv run python -m eval_runner.main \
  --agent snp.customer_service.zalo \
  --dataset datasets/customer_service/regression_v1.jsonl
```

Exit code `0` means all cases passed. Exit code `1` means one or more cases
failed (or a configuration error occurred). CI should fail on non-zero exit.

---

### Dataset Format

Datasets are **JSONL files** — one JSON object per line. Each line is an
independent eval case:

```json
{
  "id": "cs_001",
  "input": {
    "tenant_id": "snp",
    "channel": "zalo",
    "user_id": "test_user",
    "thread_id": "test_thread_001",
    "message": "hello"
  },
  "expected": {
    "must_contain": ["Hello from snp.customer_service.zalo"],
    "status": "completed"
  },
  "metadata": {
    "category": "smoke"
  }
}
```

| Field | Description |
|---|---|
| `id` | Stable unique identifier. Never reuse. |
| `input.*` | Maps directly to `RuntimeRequest` fields. |
| `expected.must_contain` | Substrings that must all appear in the answer. |
| `expected.status` | Expected `AgentRunStatus` string (e.g. `completed`). |
| `metadata.category` | Label for filtering: `smoke`, `regression`, `capability`. |

---

### Evaluators

Two deterministic evaluators run on every case:

| Evaluator | Description |
|---|---|
| `must_contain` | Each string in `expected.must_contain` must be a substring of the agent's answer. Fails if answer is `None`. |
| `status_matches` | `response.status` must equal `expected.status` (case-insensitive). |

A case passes only if **all** evaluators pass.

---

### Adding New Cases

1. Open the relevant JSONL file (e.g. `datasets/customer_service/regression_v1.jsonl`).
2. Append a new JSON line with a **unique** `id`.
3. Run `make eval` to verify the new case passes.
4. Commit both the JSONL file and any related agent changes together.

Cut a new version file (e.g. `regression_v2.jsonl`) only when the schema changes
incompatibly or a major agent behavior version is released.

---

### Exit Code Contract

| Exit code | Meaning |
|---|---|
| `0` | All cases passed. Safe to merge. |
| `1` | One or more cases failed, or the agent/dataset could not be loaded. |

---

## Future Eval Suites

Future eval suites should cover:

- Happy-path task completion.
- Known regressions and previously reported defects.
- Tool-denied and tool-unavailable flows.
- Retrieval misses and conflicting context.
- Safety escalations and human-review paths.
- LLM-as-judge quality scoring (not yet implemented).
