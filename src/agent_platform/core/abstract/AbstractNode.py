"""AbstractNode: base for non-LLM nodes (level 0).

The sealed invoke() builds a FRESH per-call NodeContext (ctx) for this call and hands
it to run(): you read the state via ctx.state, write via ctx.state.set_data(key, value)
(the execution_data bag) or ctx.state.set(field, value) (a declared field), and reach
this thread's history via ctx.history — concurrency-safe (ctx is a per-call argument,
never on the shared instance). The framework collects the staged writes for you.

    class LoopManager(AbstractNode):
        async def run(self, ctx):
            ctx.state.set_data("index", index)
            ctx.state.set_data("current", current)

Use this for pure-Python nodes. To write the messages channel from a non-LLM node,
return a partial update from run() (e.g. {"messages": [...]}); the framework merges it
with the staged writes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Mapping

from ..interface.NodeInterface import NodeInterface
from ..state.NodeContext import NodeContext


class AbstractNode(NodeInterface, ABC):
    # Opt-in: set True to get ctx.previous (the previous State) pre-resolved — NO await,
    # usable even in sync code. The framework pays one extra read per call only when set.
    LOAD_PREVIOUS: ClassVar[bool] = False

    async def invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # Run the node's logic. Its staged writes (ctx.state.set/set_data) are collected
        # by the builder; we return only any extra partial run() produces (e.g. messages).
        extra = await self.run(ctx)
        return extra or {}

    @abstractmethod
    async def run(self, ctx: NodeContext) -> Mapping[str, Any] | None:
        """Your logic: read from `ctx.state`, write via `ctx.state.set_data(key, value)`
        (bag) or `ctx.state.set(field, value)` (declared field).

        `ctx` also carries `ctx.history` — a read-only view of THIS thread's state
        history (ctx.history.previous() / .at(...) / .checkpoints()), already bound to
        the current thread, so you never handle a thread_id.

        Return None (the usual case). Return a partial dict only if you also need to write
        the messages channel (e.g. {"messages": [...]}) alongside the staged writes.
        """
        ...
