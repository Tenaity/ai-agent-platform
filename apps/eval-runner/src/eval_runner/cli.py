"""CLI entrypoint for the eval runner.

Usage:
    python -m eval_runner.main --agent snp.customer_service.zalo \\
        --dataset datasets/customer_service/regression_v1.jsonl

Exit codes:
    0 — all cases passed.
    1 — one or more cases failed, or a configuration error occurred.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eval_runner.main import run_eval
from snp_agent_testing.results import print_summary


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="eval_runner",
        description=(
            "Local-first regression evaluation runner for SNP AI Agent Platform. "
            "Runs a JSONL dataset against an agent graph in-process and reports "
            "pass/fail statistics. No real LLM calls are made."
        ),
    )

    parser.add_argument(
        "--agent",
        required=True,
        metavar="AGENT_ID",
        help=(
            "Dotted agent identifier, e.g. 'snp.customer_service.zalo'. "
            "The runner resolves this to agents/<name>/agent.yaml."
        ),
    )

    parser.add_argument(
        "--dataset",
        required=True,
        metavar="PATH",
        type=Path,
        help="Path to a .jsonl regression dataset file.",
    )

    parser.add_argument(
        "--repo-root",
        metavar="PATH",
        type=Path,
        default=None,
        help=(
            "Explicit repository root directory. Defaults to the current "
            "working directory when omitted."
        ),
    )

    return parser


def main() -> None:
    """Parse CLI arguments, run evaluation, print summary, and exit.

    Exits with code 0 on full pass, code 1 on any failure or error.
    """

    parser = build_parser()
    args = parser.parse_args()

    agent_id: str = args.agent
    dataset_path: Path = args.dataset
    repo_root: Path | None = args.repo_root

    print(f"Running eval: agent={agent_id}  dataset={dataset_path}")

    try:
        summary = run_eval(agent_id=agent_id, dataset_path=dataset_path, repo_root=repo_root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print_summary(summary)

    if summary.failed > 0:
        sys.exit(1)
