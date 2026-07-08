"""HTTP DTO: body of the `/graphs/{name}/invoke` request."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    thread_id: str = Field(..., description="Thread identifier (for state persistence).")
    input: dict[str, Any] = Field(
        default_factory=dict,
        description="Graph input. The shape depends on the invoked graph.",
    )
    include_state: bool = Field(
        default=False,
        description="If true, also return the full final state under `state`; default is the lean reply only.",
    )
