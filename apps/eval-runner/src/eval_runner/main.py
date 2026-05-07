"""Eval runner core: discover agents, load datasets, run evaluators, report results.

This module is the stable programmatic entry point into the eval runner. CLI and
future scheduler integrations call ``run_eval``; they do not re-implement the
runner loop.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from snp_agent_core.contracts import RuntimeRequest
from snp_agent_core.contracts.agent_manifest import AgentManifest
from snp_agent_core.graph.loader import load_graph_runner
from snp_agent_testing.datasets import EvalCase, load_dataset
from snp_agent_testing.evaluators import run_evaluators
from snp_agent_testing.results import EvalResult, EvalSummary, aggregate

# ---------------------------------------------------------------------------
# Agent ID → manifest resolution
# ---------------------------------------------------------------------------

def _resolve_agent_dir(agent_id: str, repo_root: Path) -> Path:
    """Map a dotted agent identifier to the agent directory path.

    Convention:
      ``snp.customer_service.zalo``  →  ``agents/customer_service/``
      ``customer_service``           →  ``agents/customer_service/``

    The leading ``snp.`` vendor prefix is stripped when present. The next
    dot-separated segment is used as the directory name. This keeps manifests
    discoverable without a central registry for now.

    Args:
        agent_id: Dotted agent identifier passed via CLI or test code.
        repo_root: Absolute path to the repository root.

    Returns:
        Path to the resolved agent directory.

    Raises:
        FileNotFoundError: If the resolved directory does not exist.
    """

    parts = agent_id.split(".")

    # Strip leading vendor prefix "snp"
    if parts and parts[0] == "snp":
        parts = parts[1:]

    if not parts:
        raise ValueError(f"Cannot resolve agent directory from agent_id '{agent_id}'.")

    # Second segment (first after vendor prefix) is the agent directory name.
    agent_dir_name = parts[0]
    agent_dir = repo_root / "agents" / agent_dir_name

    if not agent_dir.is_dir():
        raise FileNotFoundError(
            f"Agent directory not found: '{agent_dir}'. "
            f"Resolved from agent_id='{agent_id}'."
        )

    return agent_dir


def _load_manifest(agent_dir: Path) -> AgentManifest:
    """Load and validate the agent.yaml manifest from *agent_dir*.

    Args:
        agent_dir: Path to the agent's root directory.

    Returns:
        Validated ``AgentManifest``.

    Raises:
        FileNotFoundError: If agent.yaml does not exist in *agent_dir*.
        ValueError: If agent.yaml content is invalid.
    """

    manifest_path = agent_dir / "agent.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"agent.yaml not found in '{agent_dir}'.")

    raw: Any = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return AgentManifest.model_validate(raw)


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_eval(agent_id: str, dataset_path: Path, repo_root: Path | None = None) -> EvalSummary:
    """Run the full regression eval for *agent_id* against *dataset_path*.

    Steps:
    1. Resolve the agent directory and load its manifest.
    2. Build a ``GraphRunner`` from the manifest's graph import path.
    3. Load and validate the dataset JSONL.
    4. For each case, invoke the graph in-process and run all evaluators.
    5. Aggregate per-case results into an ``EvalSummary``.

    No real LLM calls are made. No external APIs are contacted. The graph
    must be deterministic for regression results to be stable.

    Args:
        agent_id: Dotted agent identifier, e.g. ``snp.customer_service.zalo``.
        dataset_path: Path to the ``.jsonl`` regression dataset.
        repo_root: Optional repository root override (defaults to CWD).

    Returns:
        ``EvalSummary`` with aggregated pass/fail statistics.
    """

    root = repo_root or Path.cwd()

    # 1. Resolve manifest
    agent_dir = _resolve_agent_dir(agent_id, root)
    manifest = _load_manifest(agent_dir)

    # 2. Build graph runner (in-process, no HTTP server)
    runner = load_graph_runner(manifest)

    # 3. Load dataset
    cases: list[EvalCase] = load_dataset(dataset_path)

    if not cases:
        print("Warning: dataset is empty — no cases to evaluate.", file=sys.stderr)

    # 4. Evaluate each case
    eval_results: list[EvalResult] = []

    for case in cases:
        request = RuntimeRequest(
            tenant_id=case.input.tenant_id,
            channel=case.input.channel,
            user_id=case.input.user_id,
            thread_id=case.input.thread_id,
            message=case.input.message,
        )

        response = runner.invoke(request)
        evaluator_results = run_evaluators(case, response)

        case_passed = all(r.passed for r in evaluator_results)

        if not case_passed:
            for er in evaluator_results:
                if not er.passed:
                    print(f"  FAIL [{case.id}] {er.evaluator}: {er.reason}")

        eval_results.append(
            EvalResult(
                case_id=case.id,
                passed=case_passed,
                evaluator_results=evaluator_results,
            )
        )

    # 5. Aggregate and return
    return aggregate(eval_results)


# ---------------------------------------------------------------------------
# __main__ entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from eval_runner.cli import main

    main()
