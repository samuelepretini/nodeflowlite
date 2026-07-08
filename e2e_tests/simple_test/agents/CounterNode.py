"""Stub node — level 0 (no LLM), via AbstractNode.

Pure-Python node for deterministic work: counters, validation, formatting, I/O, ETL
steps. No model, no tools. The framework hands run() a FRESH per-call NodeContext (ctx):
read from `ctx.state`, write with `ctx.state.set_data(key, value)`, reach this thread's
history via `ctx.history` — no dict to build, nothing to construct, concurrency-safe.

(To write the messages channel or a declared state field instead, implement
NodeInterface directly and return that partial update.)
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.NodeContext import NodeContext


class CounterNode(AbstractNode):
    async def run(self, ctx: NodeContext) -> None:
        # TODO your pure-Python logic: read with ctx.state.get(...) /
        # ctx.state.execution_data, write with ctx.state.set_data("key", value).
        count = ctx.state.execution_data.get("count", 0) + 1
        ctx.state.set_data("count", count)
