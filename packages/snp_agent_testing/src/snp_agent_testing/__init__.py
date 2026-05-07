"""snp_agent_testing: deterministic evaluation helpers for agent regression suites.

Public API:
- Dataset loading: ``EvalCase``, ``load_dataset``
- Evaluators: ``EvaluatorResult``, ``must_contain_evaluator``,
  ``status_matches_evaluator``, ``run_evaluators``
- Results: ``EvalResult``, ``EvalSummary``, ``aggregate``, ``print_summary``
"""

from snp_agent_testing.datasets import (
    EvalCase,
    EvalCaseExpected,
    EvalCaseInput,
    EvalCaseMetadata,
    load_dataset,
)
from snp_agent_testing.evaluators import (
    EvaluatorResult,
    must_contain_evaluator,
    run_evaluators,
    status_matches_evaluator,
)
from snp_agent_testing.results import (
    EvalResult,
    EvalSummary,
    aggregate,
    print_summary,
)

__all__ = [
    "EvalCase",
    "EvalCaseExpected",
    "EvalCaseInput",
    "EvalCaseMetadata",
    "EvalResult",
    "EvalSummary",
    "EvaluatorResult",
    "aggregate",
    "load_dataset",
    "must_contain_evaluator",
    "print_summary",
    "run_evaluators",
    "status_matches_evaluator",
]
