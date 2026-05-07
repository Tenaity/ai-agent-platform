# Customer Service Regression Datasets

This directory holds versioned regression datasets for the `customer_service` agent.
Each dataset version is an immutable JSONL file; never edit a published version in place.

## Dataset Schema

Each line in a `.jsonl` file is a self-contained eval case:

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

### Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Stable unique case identifier. Do not reuse. |
| `input.tenant_id` | string | Tenant routing identifier. |
| `input.channel` | string | Ingress channel (`zalo`, `api`, `web`). |
| `input.user_id` | string | Test user identifier. |
| `input.thread_id` | string | Test thread identifier (unique per case). |
| `input.message` | string | User message sent to the agent. |
| `expected.must_contain` | list[str] | Substrings that must appear in the agent's answer. |
| `expected.status` | string | Expected `AgentRunStatus` value (e.g. `completed`). |
| `metadata.category` | string | Label for filtering (`smoke`, `regression`, `capability`). |

## Versioning

- `regression_v1.jsonl` — PR-006 initial smoke suite (5 cases, all deterministic).

When adding new cases, append to the current version file. Cut a new version file (`regression_v2.jsonl`) only when the dataset shape changes incompatibly.

## Running

```bash
make eval AGENT=snp.customer_service.zalo DATASET=datasets/customer_service/regression_v1.jsonl
```

See `docs/eval-playbook.md` for the full local regression workflow.
