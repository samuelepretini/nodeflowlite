"""Interface: factory for the graph provider.

`open()` opens and manages the provider's life cycle (e.g. connection to the
Postgres checkpointer, building the graphs from the YAMLs) and returns an
asynchronous context manager that, once opened, yields a GraphProviderInterface.

Unlike a simple function alias, being an interface with a method, the
implementations explicitly inherit from it and can keep their configuration
(graphs folder, DB URI, ...) in their own constructor.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable

from .GraphProviderInterface import GraphProviderInterface


@runtime_checkable
class GraphProviderFactoryInterface(Protocol):
    def open(self) -> AbstractAsyncContextManager[GraphProviderInterface]:
        """Opens and manages the life cycle of the graph provider."""
        ...
