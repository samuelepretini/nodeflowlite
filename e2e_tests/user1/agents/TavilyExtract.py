"""Node L0 — web extraction for the current row (no LLM).

FAKE for now: fabricates a bit of text from the row, so the flow runs without a
Tavily API key. Replace the body with a real Tavily call (ideally behind a
ToolInterface).

execution_data written here:
- web_text: the text extracted from the web for `current` (empty if nothing found)
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.NodeContext import NodeContext


class TavilyExtract(AbstractNode):
    async def run(self, ctx: NodeContext) -> None:
        current = ctx.state.execution_data.get("current") or {}
        # EXAMPLE: fake web extraction — replace with a real Tavily API call.
        web_text = (
            f"Risultati web per {current.get('name', '')}: "
            f"recapito indicato presso {current.get('hint', '')}."
        )
        ctx.state.set_data("web_text", web_text)
