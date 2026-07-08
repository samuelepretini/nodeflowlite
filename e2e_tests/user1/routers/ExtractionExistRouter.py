"""Router — did the web extraction produce anything usable?

If there is web_text, hand it to the AI extractor; otherwise skip this row and go
back to LoopManager for the next one.
"""

from __future__ import annotations

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class ExtractionExistRouter(RouterInterface):
    def route(self, state: StateInterface) -> str:
        return "AIExtractor" if state.execution_data.get("web_text") else "LoopManager"
