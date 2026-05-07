"""Deterministic evaluators for agent regression evaluation.

Each evaluator is a pure function that accepts an ``EvalCase`` and a
``RuntimeResponse`` and returns an ``EvaluatorResult``. Evaluators must not
call LLMs, external APIs, or produce non-deterministic outcomes.

Extension point: add new evaluators here as plain functions, then register
them in ``run_evaluators`` or invoke them selectively from eval.yaml config.
"""

from pydantic import BaseModel, ConfigDict, Field

from snp_agent_core.contracts import RuntimeResponse
from snp_agent_testing.datasets import EvalCase


class EvaluatorResult(BaseModel):
    """Outcome of a single evaluator applied to one eval case."""

    model_config = ConfigDict(extra="forbid")

    evaluator: str = Field(..., description="Name of the evaluator that produced this result.")
    passed: bool = Field(..., description="Whether this evaluator considers the case passing.")
    reason: str = Field(..., description="Human-readable explanation for the pass/fail outcome.")


def must_contain_evaluator(case: EvalCase, response: RuntimeResponse) -> EvaluatorResult:
    """Check that every string in ``expected.must_contain`` appears in the answer.

    The check is a substring match against ``response.answer``. A missing or
    ``None`` answer fails all must_contain expectations.
    """

    name = "must_contain"
    expected_strings = case.expected.must_contain

    if not expected_strings:
        return EvaluatorResult(
            evaluator=name,
            passed=True,
            reason="No must_contain expectations defined; trivially passed.",
        )

    answer = response.answer or ""

    missing = [s for s in expected_strings if s not in answer]
    if missing:
        return EvaluatorResult(
            evaluator=name,
            passed=False,
            reason=f"Answer missing expected substrings: {missing!r}. Got: {answer!r}",
        )

    return EvaluatorResult(
        evaluator=name,
        passed=True,
        reason=f"All {len(expected_strings)} expected substring(s) found in answer.",
    )


def status_matches_evaluator(case: EvalCase, response: RuntimeResponse) -> EvaluatorResult:
    """Check that ``response.status`` equals the expected status string.

    Comparison is case-insensitive to tolerate minor serialization differences.
    """

    name = "status_matches"
    expected = case.expected.status.lower()
    actual = str(response.status).lower()

    if actual == expected:
        return EvaluatorResult(
            evaluator=name,
            passed=True,
            reason=f"Status matched: '{actual}'.",
        )

    return EvaluatorResult(
        evaluator=name,
        passed=False,
        reason=f"Status mismatch: expected '{expected}', got '{actual}'.",
    )


def run_evaluators(case: EvalCase, response: RuntimeResponse) -> list[EvaluatorResult]:
    """Run all registered deterministic evaluators against one eval case.

    A case is considered passing only if every evaluator passes. Add new
    evaluators to this list to include them in every eval run automatically.
    """

    return [
        must_contain_evaluator(case, response),
        status_matches_evaluator(case, response),
    ]
