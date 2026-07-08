"""Interface: resolves the NAMES declared in the YAML into Python objects.

This is the framework's extension point: the YAML carries only expressive names
(agents, routers, state types, reducers); the registry turns each name into the
actual object. Keeping it behind an interface lets the discovery strategy change
(explicit map now, package auto-discovery later) without touching the builder.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol, runtime_checkable

from .NodeInterface import NodeInterface
from .RouterInterface import RouterInterface


@runtime_checkable
class RegistryInterface(Protocol):
    def agent(self, name: str) -> NodeInterface:
        """The node implementation referenced by a node's `agent` name."""
        ...

    def router(self, name: str) -> RouterInterface:
        """The router implementation referenced by a conditional edge."""
        ...

    def state_type(self, name: str) -> type:
        """The Python type for a state field `type` name (e.g. 'list', 'Answer')."""
        ...

    def reducer(self, name: str) -> Callable[..., Any]:
        """The reducer function for a state field `reducer` name (e.g. 'add_messages')."""
        ...
