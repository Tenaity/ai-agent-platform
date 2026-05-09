# Agent Generator CLI

PR-017 adds a local developer CLI skeleton for generating new agent projects
from the repository templates introduced in PR-016.

The CLI is developer tooling. It is not part of the Runtime API, does not
register or deploy agents automatically, and does not call LLMs, vector
databases, production APIs, or external services.

## Usage

Run the CLI from the repository root:

```bash
PYTHONPATH=apps/agent-cli/src uv run python -m agent_cli.main create-agent \
  --template agent-basic \
  --name my_agent \
  --domain my_domain \
  --output-dir agents
```

Preview files without writing them:

```bash
PYTHONPATH=apps/agent-cli/src uv run python -m agent_cli.main create-agent \
  --template agent-rag \
  --name zalo_agent \
  --domain customer_service \
  --output-dir agents \
  --dry-run
```

Supported templates:

- `agent-basic`
- `agent-rag`
- `agent-tool`
- `agent-full-demo`

## Rendering

The generator performs deterministic string replacement only. It does not use
Jinja or any external template engine.

Supported placeholders include:

- `{{agent_name}}`
- `{{agent_id}}`
- `{{agent_module}}`
- `{{domain}}`
- `{{graph_runner_class}}`
- `{{owner}}`
- `{{package_name}}`
- `{{state_class}}`

The generated `agent_id` format is:

```text
snp.<domain>.<agent_name>
```

For example, `--domain customer_service --name zalo_agent` produces:

```text
snp.customer_service.zalo_agent
```

## Safety Checks

The generator is intentionally conservative:

- unknown templates fail clearly
- existing target directories fail clearly
- directories are created recursively
- files are never overwritten
- hidden files are ignored
- generated projects still require review, tests, and evals before use

Generated projects are scaffolds. After generation, review the files, add
domain-specific tests and datasets, and run the standard acceptance checks.
