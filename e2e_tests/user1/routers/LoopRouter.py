"""Router — is there a current row to process, or are we done?

Reads `current` (set by LoopManager): if it's a row, process it (WebExtract);
if it's None (rows finished), finish (END).
"""

from __future__ import annotations

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class LoopRouter(RouterInterface):
    def route(self, state: StateInterface) -> str:
        return "WebExtract" if state.execution_data.get("current") is not None else "END"
