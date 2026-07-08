"""Interface: a router decides the next node from the current state.

A router is the counterpart of a node, with a different responsibility:
- a node transforms the state          -> NodeInterface.invoke(state) -> update
- a router decides where to go next     -> RouterInterface.route(state) -> node name

Routers sit on conditional edges. They are referenced by name in the YAML and their
logic lives in Python (the YAML only carries expressive names, no logic).

Design choices:
- Input is the current state, read-only.
- Output is the name of the next node (e.g. "worker") or "END" to finish the graph.
- Synchronous: routing is a pure decision over the state, with no I/O.
- Framework-free: a domain contract. The builder wraps an implementation as a
  LangGraph conditional edge.

A loop is modelled as a cycle in the topology plus a router that decides whether to
continue or exit: e.g. judge -> JudgeRouter -> worker (loop) | END (exit).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .StateInterface import StateInterface


@runtime_checkable
class RouterInterface(Protocol):
    def route(self, state: StateInterface) -> str:
        """Return the name of the next node, or "END" to finish."""
        ...
