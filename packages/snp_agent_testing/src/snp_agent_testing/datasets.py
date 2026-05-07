"""Dataset loading and validation for agent regression evaluation.

Each dataset is a JSONL file where every line is a self-contained eval case.
Cases are validated at load time via Pydantic so runner code can trust the
types without defensive checks.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvalCaseInput(BaseModel):
    """Structured input payload for an eval case.

    Maps directly to the fields accepted by RuntimeRequest so cases can be
    promoted to real invocations without transformation.
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(..., description="Tenant routing identifier.")
    channel: str = Field(..., description="Ingress channel, e.g. zalo, api.")
    user_id: str = Field(..., description="Stable user identifier for the test.")
    thread_id: str = Field(..., description="Conversation thread identifier.")
    message: str = Field(..., description="User message sent to the agent.")


class EvalCaseExpected(BaseModel):
    """Expected outcome for an eval case.

    ``must_contain`` is a list of substrings that must appear in the agent's
    answer. ``status`` is the expected AgentRunStatus string value.
    """

    model_config = ConfigDict(extra="forbid")

    must_contain: list[str] = Field(
        default_factory=list,
        description="Substrings that must all appear in the agent's final answer.",
    )
    status: str = Field(..., description="Expected AgentRunStatus value, e.g. 'completed'.")


class EvalCaseMetadata(BaseModel):
    """Optional metadata attached to an eval case for filtering and reporting."""

    model_config = ConfigDict(extra="allow")

    category: str = Field(default="untagged", description="Category label, e.g. smoke, regression.")


class EvalCase(BaseModel):
    """A single regression eval case loaded from a JSONL dataset file.

    Each case is self-contained: it carries the agent input, the expected
    outcome, and lightweight metadata. The runner translates ``input`` into a
    ``RuntimeRequest`` and validates the response against ``expected``.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Stable unique identifier for this eval case.")
    input: EvalCaseInput
    expected: EvalCaseExpected
    metadata: EvalCaseMetadata = Field(default_factory=EvalCaseMetadata)


def load_dataset(path: Path) -> list[EvalCase]:
    """Load and validate a JSONL eval dataset from *path*.

    Each non-empty line must be valid JSON that deserializes into an
    ``EvalCase``. Lines that fail JSON parsing or Pydantic validation raise
    ``ValueError`` with the offending line number in the message.

    Args:
        path: Absolute or relative path to the ``.jsonl`` dataset file.

    Returns:
        Ordered list of validated ``EvalCase`` objects.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If any line cannot be parsed or validated.
    """
    import json

    cases: list[EvalCase] = []
    text = path.read_text(encoding="utf-8")

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        try:
            data: Any = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Dataset line {lineno}: invalid JSON — {exc}") from exc

        try:
            cases.append(EvalCase.model_validate(data))
        except Exception as exc:
            raise ValueError(f"Dataset line {lineno}: validation error — {exc}") from exc

    return cases
