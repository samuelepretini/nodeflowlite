"""HTTP DTO: response of the `/graphs/{name}/invoke` request."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class InvokeResponse(BaseModel):
    graph: str
    thread_id: str
    reply: Any = None  # content of the last message: the answer to the last input, ready to use
    state: dict[str, Any] | None = None  # full final state, only when the request asks for it
