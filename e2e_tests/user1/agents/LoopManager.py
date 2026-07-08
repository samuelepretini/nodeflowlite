"""Node L0 — advances the loop to the next row (no LLM).

The hub of the loop: bumps `index` and sets `current` to the next row (or None when
the rows are finished). The LoopRouter then decides whether to process `current` or
stop. Every path in the graph returns here to move on to the next row.

execution_data written here:
- index:   incremented by one
- current: rows[index], or None when there are no more rows
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.NodeContext import NodeContext


class LoopManager(AbstractNode):
    async def run(self, ctx: NodeContext) -> None:
        bag = ctx.state.execution_data
        rows = bag.get("rows", [])
        index = bag.get("index", -1) + 1
        current = rows[index] if index < len(rows) else None
        ctx.state.set_data("index", index)
        ctx.state.set_data("current", current)
