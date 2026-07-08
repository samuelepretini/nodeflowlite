"""DTO of an entire graph: in-memory representation of a graphs/*.yaml file.

Immutable value object produced by the loader. It is the "bridge" between the YAML
(text) and the builder (which will build the LangGraph StateGraph): the builder
works on this model, not on the text.
"""

from __future__ import annotations

from dataclasses import dataclass

from .EdgeDTO import EdgeDTO
from .NodeDTO import NodeDTO
from .StateFieldDTO import StateFieldDTO


@dataclass(frozen=True)
class GraphDTO:
    name: str
    state: tuple[StateFieldDTO, ...]
    nodes: tuple[NodeDTO, ...]
    edges: tuple[EdgeDTO, ...]          # SimpleEdgeDTO | ConditionalEdgeDTO
    description: str | None = None
    version: int | None = None
