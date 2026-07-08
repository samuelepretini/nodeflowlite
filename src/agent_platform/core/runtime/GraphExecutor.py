"""GraphExecutor: coordinator for executing a use-case (a graph).

It receives its tools as INTERFACES (Inversion of Control / Dependency Injection):
it does not know which concrete implementations sit behind them (FastAPI, LangGraph, ...).
It is created PER-REQUEST, with that request's channel injected into the
constructor.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..interface.ConnectionInterface import ConnectionInterface
from ..interface.GraphRuntimeInterface import GraphRuntimeInterface


class GraphExecutor:
    def __init__(self, graph: GraphRuntimeInterface, channel: ConnectionInterface):
        self._graph = graph        # what to execute   (interface)
        self._channel = channel    # where to emit     (interface)

    async def run(self, input: Mapping[str, Any], *, thread_id: str) -> None:
        result = await self._graph.ainvoke(input, thread_id=thread_id)
        await self._channel.send(result)   # it does not know FastAPI is behind it
