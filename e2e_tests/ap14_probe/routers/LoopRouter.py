"""Loop router for the AP-14 probe.

Pure, synchronous decision: keep looping back to `probe` until the counter reaches
LIMIT, then END. The counter lives in the execution_data bag the node writes.
"""

from __future__ import annotations

from typing import ClassVar

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class LoopRouter(RouterInterface):
    LIMIT: ClassVar[int] = 3

    def route(self, state: StateInterface) -> str:
        count = state.execution_data.get("count", 0)
        return "probe" if count < self.LIMIT else "END"
