# Skills Showcase

PR-026 adds metadata-driven skills so the Telegram demo can show reusable
workflow capability templates without real LLM calls, production integrations,
or deployment.

Skills describe what a workflow should do. They do not execute arbitrary code.

## Contracts

`snp_agent_core.skills` defines:

- `SkillStep`: one documented workflow step
- `SkillSpec`: metadata for a reusable skill template
- `SkillRegistry`: in-memory skill registry
- `load_skill_file`: load one `skill.yaml`
- `load_skills_from_directory`: load `*/skill.yaml` files under `skills/`

Skill files are YAML metadata only. The loader validates them with Pydantic and
does not import or execute code from skill directories.

## Sample Skills

This PR adds:

- `customer_service_checklist`
- `container_tracking_triage`
- `support_ticket_creation`

Each skill documents a small ordered workflow that future PRs can wire into
agent graph execution.

## Telegram Commands

The Telegram worker is only the demo UI. It composes the reusable skill registry
through `TelegramSkillsService`.

```text
/skill list
/skill show <skill_id>
/skill run <skill_id>
```

`/skill run` returns a deterministic simulated execution summary. It does not
call an LLM, execute tools, call external APIs, or modify runtime state.

## Non-Goals

- No arbitrary code execution from skills
- No real LLM calls
- No real tool execution from the skill runner
- No production API calls
- No MCP/A2A/ACP implementation
- No database persistence
- No webhook or deployment

Future PRs can wire skill metadata into LangGraph workflows, add richer skill
selection, and define policies for which agents may use which skills.
