"""HTTP DTO: a thread's checkpoint index (`/state/history` response).

The lightweight, newest-first list the caller picks from before asking for a full state
(via `/state/at/{checkpoint_id}`). Carries graph/thread identity plus the rows.
"""

from __future__ import annotations

from pydantic import BaseModel

from .CheckpointResponse import CheckpointResponse


class CheckpointListResponse(BaseModel):
    graph: str
    thread_id: str
    checkpoints: list[CheckpointResponse]
