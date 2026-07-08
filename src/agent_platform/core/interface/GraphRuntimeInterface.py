"""Interface: a compiled graph ready for execution.

It is the only thing the HTTP routes know how to use. Adapting from the real
LangGraph graph (building the `config` with the `thread_id`, serializing the state
to JSON, etc.) is the responsibility of `core`.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from .StateHistoryInterface import StateHistoryInterface
from .ThreadStateInterface import ThreadStateInterface


@runtime_checkable
class GraphRuntimeInterface(Protocol):
    async def ainvoke(self, input: Mapping[str, Any], *, thread_id: str) -> Mapping[str, Any]:
        """Runs the graph to completion and returns the final state (JSON-able)."""
        ...

    async def get_state(self, *, thread_id: str) -> ThreadStateInterface:
        """Returns the current persisted state of the thread."""
        ...

    def history(self, thread_id: str) -> StateHistoryInterface:
        """Returns a read-only view over the thread's state history."""
        ...
