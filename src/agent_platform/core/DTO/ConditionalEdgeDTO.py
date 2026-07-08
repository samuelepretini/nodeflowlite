"""DTO of a conditional edge: a router function decides the next node.

`router` is the name of a Python function (state) -> node name, resolved by the
registry. `targets` lists (optionally) the reachable nodes, useful for validation
and for the mapping in LangGraph.
"""

from __future__ import annotations

from dataclasses import dataclass

from .EdgeDTO import EdgeDTO


@dataclass(frozen=True)
class ConditionalEdgeDTO(EdgeDTO):
    router: str                          # name of the routing function
    targets: tuple[str, ...] = ()        # reachable nodes (empty = not declared)
