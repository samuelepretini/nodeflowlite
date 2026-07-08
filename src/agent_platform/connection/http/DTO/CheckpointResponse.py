"""HTTP DTO: one checkpoint row in a thread's history index.

The JSON-able mirror of the core `StateCheckpoint` frozen dataclass: a lightweight
"menu row" (identity + position, no state values). Built from a `StateCheckpoint` in
the route, listed inside `CheckpointListResponse`.
"""

from __future__ import annotations

from pydantic import BaseModel


class CheckpointResponse(BaseModel):
    checkpoint_id: str
    node: str
    step: int
    created_at: str
