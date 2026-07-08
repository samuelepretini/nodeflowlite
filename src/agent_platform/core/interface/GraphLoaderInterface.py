"""Interface: reads a declarative graph file and produces its DTO.

The loader is the bridge between the YAML *text* and the typed graph model
(`GraphDTO`). It only parses and validates the structure; it does NOT resolve any
name into a Python object (agents, routers, types, reducers stay as strings) — that
is the registry's job. So downstream code (the builder) works on the DTO, never on
the raw file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..DTO.GraphDTO import GraphDTO


@runtime_checkable
class GraphLoaderInterface(Protocol):
    def load(self, path: Path) -> GraphDTO:
        """Parse a single graph file into a GraphDTO (raises on malformed input)."""
        ...
