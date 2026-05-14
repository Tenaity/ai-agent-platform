"""Telegram-facing skills showcase service."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from snp_agent_core.skills import (
    SkillNotFoundError,
    SkillRegistry,
    SkillSpec,
    load_skills_from_directory,
)
from telegram_worker.commands import ParsedTelegramCommand, TelegramCommand

DEFAULT_SKILLS_ROOT: Final[Path] = Path("skills")


class TelegramSkillsService:
    """Local Telegram demo service for metadata-only skill commands."""

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        """Create a service backed by the provided or default skill registry."""

        self._registry = registry or load_skills_from_directory(DEFAULT_SKILLS_ROOT)

    def handle(self, parsed: ParsedTelegramCommand) -> str | None:
        """Return a local response for skill commands, or `None` if not handled."""

        if parsed.command != TelegramCommand.SKILL:
            return None

        subcommand, _, rest = parsed.args.strip().partition(" ")
        match subcommand.casefold():
            case "list":
                return self._list()
            case "show":
                return self._show(rest)
            case "run":
                return self._run(rest)
            case "":
                return "Usage: /skill list | /skill show <skill_id> | /skill run <skill_id>"
            case _:
                return "Usage: /skill list | /skill show <skill_id> | /skill run <skill_id>"

    def _list(self) -> str:
        skills = self._registry.list()
        if not skills:
            return "No skills are registered."
        lines = ["Available skills:"]
        lines.extend(f"- {skill.id}: {skill.name}" for skill in skills)
        return "\n".join(lines)

    def _show(self, skill_id: str) -> str:
        normalized = skill_id.strip()
        if not normalized:
            return "Usage: /skill show <skill_id>"
        try:
            skill = self._registry.get(normalized)
        except SkillNotFoundError as exc:
            return str(exc)
        return _format_skill(skill)

    def _run(self, skill_id: str) -> str:
        normalized = skill_id.strip()
        if not normalized:
            return "Usage: /skill run <skill_id>"
        try:
            skill = self._registry.get(normalized)
        except SkillNotFoundError as exc:
            return str(exc)

        lines = [
            f"Simulated skill run: {skill.id}",
            "No LLM, tool, or external API was called.",
            "Steps:",
        ]
        lines.extend(f"- {step.id}: simulated" for step in skill.steps)
        return "\n".join(lines)


def _format_skill(skill: SkillSpec) -> str:
    lines = [
        f"Skill: {skill.id}",
        f"name={skill.name}",
        f"version={skill.version}",
        f"domain={skill.domain}",
        f"description={skill.description}",
        "steps:",
    ]
    lines.extend(f"- {step.id}: {step.title} - {step.description}" for step in skill.steps)
    return "\n".join(lines)
