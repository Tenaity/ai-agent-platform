"""Integration tests for the eval runner — end-to-end run_eval flows.

These tests call run_eval() directly (in-process) against the real
customer_service graph. No LLMs, no external APIs, no LangSmith.
"""

import json
from pathlib import Path

import pytest

from eval_runner.main import run_eval
from snp_agent_testing.results import EvalSummary

# Repository root relative to this test file (tests/ is one level below root)
REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_V1 = REPO_ROOT / "datasets" / "customer_service" / "regression_v1.jsonl"


# ---------------------------------------------------------------------------
# Happy-path: full regression_v1 dataset should pass 100%
# ---------------------------------------------------------------------------


def test_run_eval_regression_v1_all_pass() -> None:
    """run_eval against regression_v1.jsonl returns 5 passing cases."""

    summary = run_eval(
        agent_id="snp.customer_service.zalo",
        dataset_path=DATASET_V1,
        repo_root=REPO_ROOT,
    )

    assert isinstance(summary, EvalSummary)
    assert summary.total == 5
    assert summary.passed == 5
    assert summary.failed == 0
    assert summary.pass_rate == pytest.approx(1.0)


def test_run_eval_without_vendor_prefix() -> None:
    """run_eval resolves agent_id='customer_service' (no prefix) correctly."""

    summary = run_eval(
        agent_id="customer_service",
        dataset_path=DATASET_V1,
        repo_root=REPO_ROOT,
    )

    assert summary.total == 5
    assert summary.failed == 0


# ---------------------------------------------------------------------------
# Failing dataset: cases that no graph can satisfy → failure status
# ---------------------------------------------------------------------------


def test_run_eval_returns_failure_when_cases_fail(tmp_path: Path) -> None:
    """run_eval returns failed > 0 when expected substrings are not in the answer."""

    # This case expects a string the deterministic graph will never produce.
    failing_case = {
        "id": "cs_fail_001",
        "input": {
            "tenant_id": "snp",
            "channel": "zalo",
            "user_id": "test_user",
            "thread_id": "thread_fail_001",
            "message": "hello",
        },
        "expected": {
            "must_contain": ["NEVER_IN_ANY_GRAPH_OUTPUT_XYZ_12345"],
            "status": "completed",
        },
        "metadata": {"category": "regression"},
    }

    dataset_path = tmp_path / "failing_dataset.jsonl"
    dataset_path.write_text(json.dumps(failing_case), encoding="utf-8")

    summary = run_eval(
        agent_id="snp.customer_service.zalo",
        dataset_path=dataset_path,
        repo_root=REPO_ROOT,
    )

    assert summary.total == 1
    assert summary.failed == 1
    assert summary.passed == 0
    assert summary.pass_rate == pytest.approx(0.0)


def test_run_eval_mixed_pass_and_fail(tmp_path: Path) -> None:
    """run_eval correctly tallies partial pass/fail in a mixed dataset."""

    passing_case = {
        "id": "cs_mix_pass",
        "input": {
            "tenant_id": "snp",
            "channel": "zalo",
            "user_id": "u1",
            "thread_id": "t_mix_pass",
            "message": "hello",
        },
        "expected": {
            "must_contain": ["Hello from snp.customer_service.zalo"],
            "status": "completed",
        },
        "metadata": {"category": "smoke"},
    }

    failing_case = {
        "id": "cs_mix_fail",
        "input": {
            "tenant_id": "snp",
            "channel": "zalo",
            "user_id": "u2",
            "thread_id": "t_mix_fail",
            "message": "hello",
        },
        "expected": {
            "must_contain": ["THIS_WILL_NEVER_APPEAR"],
            "status": "completed",
        },
        "metadata": {"category": "regression"},
    }

    dataset_path = tmp_path / "mixed.jsonl"
    dataset_path.write_text(
        json.dumps(passing_case) + "\n" + json.dumps(failing_case),
        encoding="utf-8",
    )

    summary = run_eval(
        agent_id="snp.customer_service.zalo",
        dataset_path=dataset_path,
        repo_root=REPO_ROOT,
    )

    assert summary.total == 2
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.pass_rate == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_run_eval_raises_for_unknown_agent(tmp_path: Path) -> None:
    """run_eval raises FileNotFoundError for a non-existent agent directory."""

    dataset_path = tmp_path / "empty.jsonl"
    dataset_path.write_text("", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="Agent directory not found"):
        run_eval(
            agent_id="snp.nonexistent_agent.zalo",
            dataset_path=dataset_path,
            repo_root=REPO_ROOT,
        )


def test_run_eval_raises_for_missing_dataset() -> None:
    """run_eval raises FileNotFoundError for a missing dataset path."""

    with pytest.raises(FileNotFoundError):
        run_eval(
            agent_id="snp.customer_service.zalo",
            dataset_path=Path("/no/such/file.jsonl"),
            repo_root=REPO_ROOT,
        )
