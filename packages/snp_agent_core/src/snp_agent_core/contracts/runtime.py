"""Runtime-facing contracts shared by apps and platform packages."""

from typing import Literal

from pydantic import BaseModel


class RuntimeHealth(BaseModel):
    """Runtime health state suitable for API responses and probes."""

    status: Literal["ok", "degraded"]
