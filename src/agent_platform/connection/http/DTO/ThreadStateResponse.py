"""HTTP DTO: persisted state of a thread (`/threads/{tid}/state` response)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ThreadStateResponse(BaseModel):
    graph: str
    thread_id: str
    values: dict[str, Any]
    next: list[str]
