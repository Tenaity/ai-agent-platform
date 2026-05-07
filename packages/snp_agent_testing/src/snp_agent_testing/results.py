"""Aggregation and reporting for eval run results.

``EvalResult`` captures the per-case outcome. ``EvalSummary`` aggregates a
full run. ``print_summary`` renders a human-readable table to stdout.
"""

from pydantic import BaseModel, ConfigDict, Field

from snp_agent_testing.evaluators import EvaluatorResult


class EvalResult(BaseModel):
    """Outcome of running all evaluators against a single eval case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., description="Identifier of the eval case.")
    passed: bool = Field(
        ...,
        description="True only if every evaluator returned passed=True.",
    )
    evaluator_results: list[EvaluatorResult] = Field(
        default_factory=list,
        description="Per-evaluator outcomes for this case.",
    )


class EvalSummary(BaseModel):
    """Aggregated statistics for a completed eval run."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total number of eval cases executed.")
    passed: int = Field(..., description="Number of cases where all evaluators passed.")
    failed: int = Field(..., description="Number of cases where at least one evaluator failed.")
    pass_rate: float = Field(
        ...,
        description="Fraction of cases that passed, in the range [0.0, 1.0].",
    )


def aggregate(results: list[EvalResult]) -> EvalSummary:
    """Aggregate a list of per-case results into an ``EvalSummary``.

    Args:
        results: One ``EvalResult`` per evaluated case.

    Returns:
        ``EvalSummary`` with total, passed, failed, and pass_rate computed.
    """

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = passed / total if total > 0 else 0.0

    return EvalSummary(total=total, passed=passed, failed=failed, pass_rate=pass_rate)


def print_summary(summary: EvalSummary) -> None:
    """Print a formatted summary table to stdout.

    The output includes total, passed, failed, and pass_rate. Each failed case
    is expected to be reported individually by the caller before calling this
    function.
    """

    sep = "─" * 45
    print(sep)
    print(f"  {'total':<12}: {summary.total}")
    print(f"  {'passed':<12}: {summary.passed}")
    print(f"  {'failed':<12}: {summary.failed}")
    print(f"  {'pass_rate':<12}: {summary.pass_rate * 100:.2f}%")
    print(sep)

    if summary.failed == 0:
        print("All cases passed.")
    else:
        print(f"{summary.failed} case(s) FAILED.")
