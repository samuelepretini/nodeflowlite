"""Example router: decides whether the quality loop continues or stops.

It sits on the conditional edge out of the `judge` node and reads the state the
JudgeAgent wrote (`verdict`, `attempts`). It carries NO LLM and NO I/O: routing is
a pure, synchronous decision over the state, which is exactly RouterInterface.

The loop exits (-> END) when the judge is satisfied (verdict OK) or the worker has
used up its attempts (MAX_ATTEMPTS); otherwise it loops back to the worker, which
will see the judge's critique (appended to `messages` by JudgeAgent) and retry.

`MAX_ATTEMPTS` lives here, not in the JudgeAgent: it is a routing policy, not part
of evaluating a single answer.
"""

from __future__ import annotations

from typing import ClassVar

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class JudgeRouter(RouterInterface):
    MAX_ATTEMPTS: ClassVar[int] = 3

    def route(self, state: StateInterface) -> str:
        verdict = state.get("verdict", "")
        attempts = state.get("attempts", 0)
        if verdict.startswith("OK") or attempts >= self.MAX_ATTEMPTS:
            return "END"
        return "worker"
