"""Interface: turns a graph DTO into a runnable graph.

The builder is where the typed graph model (`GraphDTO`) meets the engine: it
resolves the declared names through the registry, assembles the LangGraph
StateGraph (state schema + nodes + edges), compiles it, and returns it behind the
`GraphRuntimeInterface` port — so the rest of the system never sees LangGraph.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..DTO.GraphDTO import GraphDTO
from .GraphRuntimeInterface import GraphRuntimeInterface


@runtime_checkable
class GraphBuilderInterface(Protocol):
    def build(self, graph: GraphDTO) -> GraphRuntimeInterface:
        """Build and compile a graph DTO into a ready-to-run runtime."""
        ...
