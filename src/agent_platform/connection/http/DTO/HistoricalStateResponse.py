"""HTTP DTO: a historical State (previous / at-checkpoint responses).

Mirrors `ThreadStateResponse` (graph, thread_id, values) but for a state read from the
history. A historical snapshot is a frozen super-step, not the live cursor, so it carries
no `next` (that is a property of the current head, surfaced by `ThreadStateResponse`).
The optional `checkpoint_id` echoes which checkpoint was resolved (None for `previous`).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HistoricalStateResponse(BaseModel):
    graph: str
    thread_id: str
    values: dict[str, Any]
    checkpoint_id: str | None = None
