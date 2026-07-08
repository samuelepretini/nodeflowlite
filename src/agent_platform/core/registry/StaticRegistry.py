"""StaticRegistry: name -> object resolution from explicit maps.

The composition root hands it the user's classes by name (agents/routers) plus any
custom types/reducers; the registry resolves the names the YAML declares. Common
types and reducers (str/int/.../add_messages) are shipped as BUILTINS, so the user
never re-declares them — they just write the name in the YAML.

Agents and routers are instantiated lazily and cached: the registry returns ready
objects, so the builder only asks "give me the agent named X".
"""

from __future__ import annotations

from typing import Any, Callable

from langgraph.graph.message import add_messages

from ..interface.NodeInterface import NodeInterface
from ..interface.RegistryInterface import RegistryInterface
from ..interface.RouterInterface import RouterInterface
from ..state.reducers import merge_dicts


class StaticRegistry(RegistryInterface):
    # Shipped by the framework so the user never re-declares the basics.
    _BUILTIN_TYPES: dict[str, type] = {
        "str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict,
    }
    _BUILTIN_REDUCERS: dict[str, Callable[..., Any]] = {
        "add_messages": add_messages,
        "merge": merge_dicts,  # shallow dict merge — also auto-applied to execution_data
    }

    def __init__(
        self,
        *,
        agents: dict[str, type[NodeInterface]] | None = None,
        routers: dict[str, type[RouterInterface]] | None = None,
        types: dict[str, type] | None = None,
        reducers: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        self._agent_classes = dict(agents or {})
        self._router_classes = dict(routers or {})
        self._types = {**self._BUILTIN_TYPES, **(types or {})}
        self._reducers = {**self._BUILTIN_REDUCERS, **(reducers or {})}
        self._agent_cache: dict[str, NodeInterface] = {}
        self._router_cache: dict[str, RouterInterface] = {}

    def agent(self, name: str) -> NodeInterface:
        if name not in self._agent_cache:
            self._agent_cache[name] = self._get(self._agent_classes, name, "agent")()
        return self._agent_cache[name]

    def router(self, name: str) -> RouterInterface:
        if name not in self._router_cache:
            self._router_cache[name] = self._get(self._router_classes, name, "router")()
        return self._router_cache[name]

    def state_type(self, name: str) -> type:
        return self._get(self._types, name, "state type")

    def reducer(self, name: str) -> Callable[..., Any]:
        return self._get(self._reducers, name, "reducer")

    @staticmethod
    def _get(mapping: dict[str, Any], name: str, kind: str) -> Any:
        try:
            return mapping[name]
        except KeyError:
            raise ValueError(
                f"{kind} {name!r} is not registered. Available: {sorted(mapping)}"
            ) from None
