"""Tests for snp_agent_testing.evaluators — deterministic evaluator functions."""

import pytest

from snp_agent_core.contracts import RuntimeResponse
from snp_agent_core.contracts.status import AgentRunStatus
from snp_agent_testing.datasets import (
    EvalCase,
    EvalCaseExpected,
    EvalCaseInput,
    EvalCaseMetadata,
)
from snp_agent_testing.evaluators import (
    must_contain_evaluator,
    run_evaluators,
    status_matches_evaluator,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_case(
    must_contain: list[str],
    status: str = "completed",
    message: str = "hello",
) -> EvalCase:
    return EvalCase(
        id="eval_test",
        input=EvalCaseInput(
            tenant_id="snp",
            channel="zalo",
            user_id="u1",
            thread_id="t1",
            message=message,
        ),
        expected=EvalCaseExpected(must_contain=must_contain, status=status),
        metadata=EvalCaseMetadata(),
    )


def _make_response(
    answer: str | None = "Hello from snp.customer_service.zalo. stub.",
    status: AgentRunStatus = AgentRunStatus.COMPLETED,
) -> RuntimeResponse:
    return RuntimeResponse(thread_id="t1", status=status, answer=answer)


# ---------------------------------------------------------------------------
# must_contain_evaluator
# ---------------------------------------------------------------------------


def test_must_contain_passes_when_substring_present() -> None:
    """must_contain passes when all expected strings are in the answer."""

    case = _make_case(must_contain=["Hello from snp"])
    response = _make_response(answer="Hello from snp.customer_service.zalo.")
    result = must_contain_evaluator(case, response)

    assert result.passed is True
    assert result.evaluator == "must_contain"


def test_must_contain_fails_when_substring_absent() -> None:
    """must_contain fails when an expected string is missing from the answer."""

    case = _make_case(must_contain=["NEVER_IN_OUTPUT"])
    response = _make_response(answer="Hello from snp.customer_service.zalo.")
    result = must_contain_evaluator(case, response)

    assert result.passed is False
    assert "NEVER_IN_OUTPUT" in result.reason


def test_must_contain_fails_when_answer_is_none() -> None:
    """must_contain fails when the agent returns no answer."""

    case = _make_case(must_contain=["Hello"])
    response = _make_response(answer=None)
    result = must_contain_evaluator(case, response)

    assert result.passed is False


def test_must_contain_passes_with_empty_expectations() -> None:
    """must_contain trivially passes when the expected list is empty."""

    case = _make_case(must_contain=[])
    response = _make_response()
    result = must_contain_evaluator(case, response)

    assert result.passed is True


def test_must_contain_all_substrings_must_be_present() -> None:
    """must_contain requires ALL expected substrings to pass."""

    case = _make_case(must_contain=["Hello", "MISSING"])
    response = _make_response(answer="Hello from snp.customer_service.zalo.")
    result = must_contain_evaluator(case, response)

    assert result.passed is False
    assert "MISSING" in result.reason


# ---------------------------------------------------------------------------
# status_matches_evaluator
# ---------------------------------------------------------------------------


def test_status_matches_passes_on_exact_match() -> None:
    """status_matches passes when status equals the expected string."""

    case = _make_case(must_contain=[], status="completed")
    response = _make_response(status=AgentRunStatus.COMPLETED)
    result = status_matches_evaluator(case, response)

    assert result.passed is True
    assert result.evaluator == "status_matches"


def test_status_matches_fails_on_wrong_status() -> None:
    """status_matches fails when actual status differs from expected."""

    case = _make_case(must_contain=[], status="completed")
    response = _make_response(status=AgentRunStatus.FAILED)
    result = status_matches_evaluator(case, response)

    assert result.passed is False
    assert "failed" in result.reason
    assert "completed" in result.reason


def test_status_matches_is_case_insensitive() -> None:
    """status_matches comparison is case-insensitive."""

    case = _make_case(must_contain=[], status="COMPLETED")
    response = _make_response(status=AgentRunStatus.COMPLETED)
    result = status_matches_evaluator(case, response)

    assert result.passed is True


# ---------------------------------------------------------------------------
# run_evaluators
# ---------------------------------------------------------------------------


def test_run_evaluators_returns_both_results() -> None:
    """run_evaluators returns one result per registered evaluator."""

    case = _make_case(must_contain=["Hello from snp"])
    response = _make_response()
    results = run_evaluators(case, response)

    assert len(results) == 2
    evaluator_names = {r.evaluator for r in results}
    assert evaluator_names == {"must_contain", "status_matches"}


def test_run_evaluators_all_pass_on_correct_response() -> None:
    """All evaluators pass when the response satisfies every expectation."""

    case = _make_case(must_contain=["Hello from snp.customer_service.zalo"])
    response = _make_response(
        answer="Hello from snp.customer_service.zalo. stub.",
        status=AgentRunStatus.COMPLETED,
    )
    results = run_evaluators(case, response)

    assert all(r.passed for r in results)


def test_run_evaluators_partial_failure() -> None:
    """run_evaluators reports individual failures even if some evaluators pass."""

    case = _make_case(must_contain=["MISSING"], status="completed")
    response = _make_response(
        answer="Hello from snp.customer_service.zalo.",
        status=AgentRunStatus.COMPLETED,
    )
    results = run_evaluators(case, response)

    passed_names = {r.evaluator for r in results if r.passed}
    failed_names = {r.evaluator for r in results if not r.passed}

    assert "status_matches" in passed_names
    assert "must_contain" in failed_names


@pytest.mark.parametrize(
    ("must_contain", "status", "answer", "run_status", "expected_all_pass"),
    [
        (["Hello"], "completed", "Hello world", AgentRunStatus.COMPLETED, True),
        (["Hello"], "failed", "Hello world", AgentRunStatus.COMPLETED, False),
        (["MISSING"], "completed", "Hello world", AgentRunStatus.COMPLETED, False),
        ([], "completed", None, AgentRunStatus.COMPLETED, True),
    ],
)
def test_run_evaluators_parametrized(
    must_contain: list[str],
    status: str,
    answer: str | None,
    run_status: AgentRunStatus,
    expected_all_pass: bool,
) -> None:
    """Parametrized table of evaluator scenarios."""

    case = _make_case(must_contain=must_contain, status=status)
    response = _make_response(answer=answer, status=run_status)
    results = run_evaluators(case, response)
    all_pass = all(r.passed for r in results)
    assert all_pass is expected_all_pass
