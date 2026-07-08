"""Router — are there any rows to process at all?

Reads execution_data after the sheet read: if there are rows, enter the loop
(LoopManager); otherwise finish (END).
"""

from __future__ import annotations

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class RowExistenceRouter(RouterInterface):
    def route(self, state: StateInterface) -> str:
        return "LoopManager" if state.execution_data.get("rows") else "END"
