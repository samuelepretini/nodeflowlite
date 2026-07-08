"""Router — is the AI extraction result valid?

If the extractor returned a usable result, format it (AIAddressFormatter); otherwise
skip this row and go back to LoopManager.
"""

from __future__ import annotations

from agent_platform.core.interface.RouterInterface import RouterInterface
from agent_platform.core.interface.StateInterface import StateInterface


class AIResultCheckRouter(RouterInterface):
    def route(self, state: StateInterface) -> str:
        extracted = (state.execution_data.get("extracted") or "").strip()
        # EXAMPLE rule: valid if non-empty and not the 'KO' marker the extractor emits.
        if extracted and not extracted.upper().startswith("KO"):
            return "AIAddressFormatter"
        return "LoopManager"
