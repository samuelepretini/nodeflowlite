"""Interface: OUTPUT channel toward the outside world.

It is a "port" (Ports & Adapters): GraphExecutor receives it and uses it to emit
results/events, WITHOUT knowing who implements it (FastAPI, CLI, queue, ...).
It stays framework-free: no FastAPI import in here.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class ConnectionInterface(Protocol):
    async def send(self, payload: Mapping[str, Any]) -> None:
        """Sends the result/message produced by the execution to the outside."""
        ...
