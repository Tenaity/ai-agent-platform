"""Tests for snp_agent_testing.datasets — dataset loading and validation."""

import json
from pathlib import Path

import pytest

from snp_agent_testing.datasets import EvalCase, load_dataset

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_CASE: dict[str, object] = {
    "id": "test_001",
    "input": {
        "tenant_id": "snp",
        "channel": "zalo",
        "user_id": "user1",
        "thread_id": "thread1",
        "message": "hello",
    },
    "expected": {
        "must_contain": ["Hello"],
        "status": "completed",
    },
    "metadata": {"category": "smoke"},
}


def _write_jsonl(tmp_path: Path, lines: list[dict[str, object]]) -> Path:
    """Write a list of dicts as JSONL to a temp file."""

    path = tmp_path / "test_dataset.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


def test_load_dataset_returns_eval_cases(tmp_path: Path) -> None:
    """load_dataset returns a list of EvalCase objects for a valid JSONL."""

    path = _write_jsonl(tmp_path, [MINIMAL_CASE])
    cases = load_dataset(path)

    assert len(cases) == 1
    case = cases[0]
    assert isinstance(case, EvalCase)
    assert case.id == "test_001"
    assert case.input.tenant_id == "snp"
    assert case.input.channel == "zalo"
    assert case.input.message == "hello"
    assert case.expected.must_contain == ["Hello"]
    assert case.expected.status == "completed"
    assert case.metadata.category == "smoke"


def test_load_dataset_multiple_cases(tmp_path: Path) -> None:
    """load_dataset returns all cases from a multi-line JSONL."""

    case2: dict[str, object] = {
        "id": "test_002",
        "input": {
            "tenant_id": "snp",
            "channel": "zalo",
            "user_id": "user1",
            "thread_id": "t2",
            "message": "hello",
        },
        "expected": {"must_contain": ["Hello"], "status": "completed"},
        "metadata": {"category": "smoke"},
    }
    path = _write_jsonl(tmp_path, [MINIMAL_CASE, case2])
    cases = load_dataset(path)

    assert len(cases) == 2
    assert cases[0].id == "test_001"
    assert cases[1].id == "test_002"


def test_load_dataset_skips_blank_lines(tmp_path: Path) -> None:
    """Blank lines in a JSONL file are silently skipped."""

    path = tmp_path / "dataset.jsonl"
    path.write_text(
        json.dumps(MINIMAL_CASE) + "\n\n   \n" + json.dumps(MINIMAL_CASE),
        encoding="utf-8",
    )
    cases = load_dataset(path)
    assert len(cases) == 2


def test_load_dataset_empty_must_contain(tmp_path: Path) -> None:
    """Cases with an empty must_contain list are valid."""

    case = {**MINIMAL_CASE, "expected": {"must_contain": [], "status": "completed"}}
    path = _write_jsonl(tmp_path, [case])
    cases = load_dataset(path)
    assert cases[0].expected.must_contain == []


def test_load_dataset_missing_metadata_uses_default(tmp_path: Path) -> None:
    """Cases missing the optional metadata block get default values."""

    case = {k: v for k, v in MINIMAL_CASE.items() if k != "metadata"}
    path = _write_jsonl(tmp_path, [case])
    cases = load_dataset(path)
    assert cases[0].metadata.category == "untagged"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_load_dataset_raises_on_invalid_json(tmp_path: Path) -> None:
    """A malformed JSON line raises ValueError with the line number."""

    path = tmp_path / "bad.jsonl"
    path.write_text("not valid json\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        load_dataset(path)


def test_load_dataset_raises_on_missing_required_field(tmp_path: Path) -> None:
    """A case missing a required field raises ValueError."""

    bad_case = {k: v for k, v in MINIMAL_CASE.items() if k != "id"}
    path = _write_jsonl(tmp_path, [bad_case])

    with pytest.raises(ValueError, match="line 1"):
        load_dataset(path)


def test_load_dataset_raises_file_not_found() -> None:
    """load_dataset raises FileNotFoundError for a missing path."""

    with pytest.raises(FileNotFoundError):
        load_dataset(Path("/nonexistent/path/dataset.jsonl"))


def test_load_dataset_real_regression_v1() -> None:
    """The committed regression_v1.jsonl loads without errors."""

    repo_root = Path(__file__).resolve().parents[1]
    dataset_path = repo_root / "datasets" / "customer_service" / "regression_v1.jsonl"

    cases = load_dataset(dataset_path)
    assert len(cases) == 5
    assert all(isinstance(c, EvalCase) for c in cases)
    # All smoke cases expect status=completed
    assert all(c.expected.status == "completed" for c in cases)
