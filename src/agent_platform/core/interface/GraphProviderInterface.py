"""Interface: resolves graphs by name. One YAML file in `graphs/` = one graph."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .GraphRuntimeInterface import GraphRuntimeInterface


@runtime_checkable
class GraphProviderInterface(Protocol):
    def get(self, name: str) -> GraphRuntimeInterface | None:
        """Returns the graph runtime, or None if the name does not exist."""
        ...

    def names(self) -> list[str]:
        """Lists the names of the available graphs."""
        ...

    def failure(self, name: str) -> str | None:
        """Why a declared graph is unavailable (it failed to build), or None.

        Lets a caller tell apart 'this graph was never declared' from 'it was
        declared but could not be built' (e.g. a misconfiguration)."""
        ...
