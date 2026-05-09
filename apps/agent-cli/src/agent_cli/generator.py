"""Agent project generation from repository templates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from agent_cli.templates import resolve_template_dir

_SAFE_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class GeneratedFile:
    """A rendered file planned or written by the generator."""

    path: Path
    dry_run: bool


@dataclass(frozen=True)
class GenerationResult:
    """Summary of files produced by a generation request."""

    target_dir: Path
    files: tuple[GeneratedFile, ...]
    dry_run: bool


@dataclass(frozen=True)
class _PlannedFile:
    source_path: Path
    target_path: Path


def generate_agent(
    *,
    template: str,
    name: str,
    domain: str,
    output_dir: Path,
    dry_run: bool = False,
    repo_root: Path | None = None,
) -> GenerationResult:
    """Generate an agent project from a template without overwriting files."""

    _validate_identifier("name", name)
    _validate_identifier("domain", domain)

    template_dir = resolve_template_dir(template, repo_root=repo_root)
    target_dir = output_dir / name
    if target_dir.exists():
        msg = f"Target directory already exists: {target_dir}."
        raise FileExistsError(msg)

    replacements = _build_replacements(name=name, domain=domain)
    planned_files = tuple(_iter_template_files(template_dir, target_dir, replacements))
    result_files = tuple(
        GeneratedFile(path=planned_file.target_path, dry_run=dry_run)
        for planned_file in planned_files
    )

    if dry_run:
        return GenerationResult(target_dir=target_dir, files=result_files, dry_run=True)

    target_dir.mkdir(parents=True, exist_ok=False)
    for planned_file in planned_files:
        planned_file.target_path.parent.mkdir(parents=True, exist_ok=True)
        if planned_file.target_path.exists():
            msg = f"Refusing to overwrite existing file: {planned_file.target_path}."
            raise FileExistsError(msg)

        rendered = _render_text(planned_file.source_path.read_text(encoding="utf-8"), replacements)
        planned_file.target_path.write_text(rendered, encoding="utf-8")

    return GenerationResult(target_dir=target_dir, files=result_files, dry_run=False)


def _iter_template_files(
    template_dir: Path,
    target_dir: Path,
    replacements: dict[str, str],
) -> list[_PlannedFile]:
    files: list[_PlannedFile] = []
    for source_path in sorted(path for path in template_dir.rglob("*") if path.is_file()):
        if any(part.startswith(".") for part in source_path.relative_to(template_dir).parts):
            continue

        relative_path = source_path.relative_to(template_dir)
        target_relative_path = _target_relative_path(relative_path)
        target_path = target_dir / target_relative_path

        # Rendering the source once during planning catches stale placeholders early.
        _render_text(source_path.read_text(encoding="utf-8"), replacements)
        files.append(_PlannedFile(source_path=source_path, target_path=target_path))
    return files


def _target_relative_path(relative_path: Path) -> Path:
    name = relative_path.name
    if name.endswith(".template"):
        name = name.removesuffix(".template")
    return relative_path.with_name(name)


def _build_replacements(*, name: str, domain: str) -> dict[str, str]:
    agent_id = f"snp.{domain}.{name}"
    class_prefix = "".join(part.capitalize() for part in name.split("_"))
    return {
        "agent_name": name,
        "agent_id": agent_id,
        "agent_module": name,
        "domain": domain,
        "graph_runner_class": f"{class_prefix}GraphRunner",
        "owner": "platform-team",
        "package_name": name,
        "state_class": f"{class_prefix}State",
    }


def _render_text(content: str, replacements: dict[str, str]) -> str:
    rendered = content
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)

    unresolved = sorted(set(re.findall(r"{{\s*[^}]+\s*}}", rendered)))
    if unresolved:
        msg = f"Unresolved template placeholders: {', '.join(unresolved)}."
        raise ValueError(msg)
    return rendered


def _validate_identifier(field: str, value: str) -> None:
    if not _SAFE_NAME_RE.fullmatch(value):
        msg = (
            f"{field} must start with a letter and contain only letters, numbers, "
            "and underscores."
        )
        raise ValueError(msg)
