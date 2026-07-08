"""Node L0 — reads the input rows into execution_data (no LLM).

FAKE for now: returns a small in-memory list, so the flow runs end-to-end without
Google credentials. Replace the body with a real Google Sheet read (ideally behind a
ToolInterface).

execution_data written here:
- rows:    list of input rows to process
- index:   current row index (-1 so the first LoopManager step lands on row 0)
- results: accumulator for the processed rows (written by SheetWriter)
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.NodeContext import NodeContext


class SheetReader(AbstractNode):
    async def run(self, ctx: NodeContext) -> None:
        # EXAMPLE: fake input rows — replace with a real Google Sheet read.
        rows = [
            {"name": "Studio Dentistico Rossi", "hint": "Milano, zona Dante"},
            {"name": "Dott. Bianchi Odontoiatra", "hint": "Roma centro"},
        ]
        ctx.state.set_data("rows", rows)
        ctx.state.set_data("index", -1)
        ctx.state.set_data("results", [])
