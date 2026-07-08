"""HTTP (FastAPI) implementation of ConnectionInterface.

In a request/response model, `send` does not "push" anything: it buffers the
payload produced by the execution, which the route then returns as the HTTP response.
It is created PER-REQUEST: one channel = one response.
"""

from __future__ import annotations

from typing import Any, Mapping

from agent_platform.core.interface.ConnectionInterface import ConnectionInterface


class HttpConnection(ConnectionInterface):
    def __init__(self) -> None:
        self._payload: dict[str, Any] | None = None

    async def send(self, payload: Mapping[str, Any]) -> None:
        self._payload = dict(payload)

    @property
    def payload(self) -> dict[str, Any]:
        return self._payload or {}
