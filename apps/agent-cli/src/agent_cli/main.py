"""Command-line entrypoint for local agent project generation."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from agent_cli.generator import generate_agent
from agent_cli.templates import SUPPORTED_TEMPLATES


def main(argv: Sequence[str] | None = None) -> int:
    """Run the agent CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "create-agent":
        try:
            result = generate_agent(
                template=args.template,
                name=args.name,
                domain=args.domain,
                output_dir=Path(args.output_dir),
                dry_run=args.dry_run,
            )
        except (FileExistsError, FileNotFoundError, ValueError) as exc:
            parser.exit(status=2, message=f"error: {exc}\n")

        verb = "Would create" if result.dry_run else "Created"
        print(f"{verb} {result.target_dir}")
        for generated_file in result.files:
            print(f" - {generated_file.path}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-cli",
        description="Generate local agent project skeletons from repository templates.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser(
        "create-agent",
        help="Create a new agent project from a template.",
    )
    create.add_argument("--template", required=True, choices=SUPPORTED_TEMPLATES)
    create.add_argument("--name", required=True)
    create.add_argument("--domain", required=True)
    create.add_argument("--output-dir", default="agents")
    create.add_argument("--dry-run", action="store_true")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
