"""Node L0 — writes the processed row to the output (no LLM).

FAKE for now: appends the result to the `results` accumulator in execution_data, so
the flow runs without Google credentials. Replace the body with a real Google Sheet
write (ideally behind a ToolInterface).

execution_data written here:
- results: the accumulator, with the current processed row appended
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.NodeContext import NodeContext


class SheetWriter(AbstractNode):
    async def run(self, ctx: NodeContext) -> None:
        bag = ctx.state.execution_data
        results = list(bag.get("results", []))
        current = bag.get("current") or {}
        results.append({**current, "formatted_address": bag.get("formatted_address", "")})
        # EXAMPLE: fake write (append to results) — replace with a real Google Sheet write.
        ctx.state.set_data("results", results)
