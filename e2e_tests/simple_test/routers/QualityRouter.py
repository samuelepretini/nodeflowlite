"""Stub router — decides whether a quality loop continues or stops.

A router carries NO LLM and NO I/O: route(state) is a pure, synchronous decision
returning the next node's name, or "END" to finish the graph. It reads the state a
judge wrote (here `verdict` / `attempts`).

The stop POLICY lives here (e.g. MAX_ATTEMPTS), not in the judge: evaluating one
answer and deciding when to give up are different responsibilities.
"""

from __future__ import annotations

from typing import ClassVar

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class QualityRouter(RouterInterface):
    MAX_ATTEMPTS: ClassVar[int] = 3

    def route(self, state: StateInterface) -> str:
        # TODO decide from the state, e.g.:
        #   if state.get("verdict", "").startswith("OK") or state.get("attempts", 0) >= self.MAX_ATTEMPTS:
        #       return "END"
        #   return "worker"
        return "END"
