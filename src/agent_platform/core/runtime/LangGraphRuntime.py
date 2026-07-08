"""LangGraphRuntime: the real GraphRuntimeInterface, backed by a compiled graph.

It is the adapter that isolates LangGraph behind the port: it owns the compiled
graph and translates our interface (ainvoke/get_state with a thread_id) into the
LangGraph calls (building the `config` with the thread_id). It replaces the
development EchoGraphRuntime.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..interface.GraphRuntimeInterface import GraphRuntimeInterface
from ..interface.StateHistoryInterface import StateHistoryInterface
from ..interface.ThreadStateInterface import ThreadStateInterface
from .LangGraphStateHistory import LangGraphStateHistory

# CHOICE: max LangGraph super-steps per single invocation (its safety cap against
# runaway loops; default would be 25). Raised to 1000 so a graph that loops over many
# items in one run (~steps-per-iteration x items) isn't cut short. Alternative: process
# one item per invocation with an external driver (then the default would suffice).
RECURSION_LIMIT = 1000


class LangGraphRuntime(GraphRuntimeInterface):
    def __init__(self, compiled: Any) -> None:
        self._compiled = compiled  # a compiled LangGraph graph

    async def ainvoke(self, input: Mapping[str, Any], *, thread_id: str) -> Mapping[str, Any]:
        return await self._compiled.ainvoke(dict(input), self._config(thread_id))

    async def get_state(self, *, thread_id: str) -> ThreadStateInterface:
        # LangGraph's StateSnapshot is structurally a ThreadStateInterface (values/next).
        return await self._compiled.aget_state(self._config(thread_id))

    def history(self, thread_id: str) -> StateHistoryInterface:
        return LangGraphStateHistory(self._compiled, thread_id)

    @staticmethod
    def _config(thread_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}
