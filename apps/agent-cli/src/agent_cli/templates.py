"""Template discovery helpers for the local agent generator CLI."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_TEMPLATES = (
    "agent-basic",
    "agent-rag",
    "agent-tool",
    "agent-full-demo",
)


def find_repo_root(start: Path | None = None) -> Path:
    """Find the repository root by walking up to the templates directory."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "templates").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    msg = "Could not find repository root containing templates/ and pyproject.toml."
    raise FileNotFoundError(msg)


def resolve_template_dir(template: str, repo_root: Path | None = None) -> Path:
    """Return the path for a supported template or raise a clear error."""

    if template not in SUPPORTED_TEMPLATES:
        supported = ", ".join(SUPPORTED_TEMPLATES)
        msg = f"Unknown template '{template}'. Supported templates: {supported}."
        raise ValueError(msg)

    root = repo_root or find_repo_root()
    template_dir = root / "templates" / template
    if not template_dir.is_dir():
        msg = f"Template '{template}' was not found at {template_dir}."
        raise FileNotFoundError(msg)
    return template_dir

