"""AbstractHookedNode: an LLM node that exposes lifecycle hooks (level 2).

The intermediate level of control for a worker, between AbstractCommonNode (level 1,
config-only) and a fully manual node (level 3, override invoke()). invoke() is sealed
and orchestrates:

    before_invoke(ctx) -> [merge onto input] -> [LLM core] -> after_invoke(ctx, result)

wrapped in a try/except that routes failures to on_error(ctx, error).

Two kinds of hook, two different jobs:
- before_invoke shapes the INPUT: it returns a partial merged onto the state the model
  sees (a Mapping of changed fields; {} = no change). It does NOT emit the output.
- after_invoke / on_error shape the OUTPUT, exactly like on_result: they RETURN the
  node's message — str (→ AIMessage) | BaseMessage (as-is) | None (suppress). The
  framework turns the return into the messages channel.

Side writes (execution_data, declared fields) go through ctx.state (set_data / set), as
everywhere. Defaults make this behave like AbstractCommonNode: before changes nothing,
after returns the raw model message, on_error re-raises (never silently swallowed).

Framework-free domain code: like its parent, it knows nothing about HTTP or DB.
"""

from __future__ import annotations

from typing import Any, Mapping, cast

from langchain_core.messages import BaseMessage

from ..interface.StateInterface import StateInterface
from ..state.NodeContext import NodeContext
from ..state.State import State
from ..state.WritableState import WritableState
from .AbstractCommonNode import AbstractCommonNode


class AbstractHookedNode(AbstractCommonNode):
    async def invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # before_invoke shapes the input: merge its partial onto the state the model sees,
        # KEEPING any output already staged (with_input shares the staged buffer).
        before = await self.before_invoke(ctx)
        if before:
            merged = cast(WritableState, ctx.state).with_input(before)
            ctx = NodeContext(state=merged, history=ctx.history, previous=ctx.previous)
        try:
            result = State(await self.ai_invoke(ctx.state))
        except Exception as error:
            return self._message_update(await self.on_error(ctx, error))
        return self._message_update(await self.after_invoke(ctx, result))

    async def before_invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        """Run before the LLM call: validate or transform the INPUT.

        Return ONLY the state fields you want the model to see changed (a partial) — the
        framework preserves the rest. Return nothing/{} to leave the input as is. Read via
        ctx.state, reach this thread's history via ctx.history. (To stash output data use
        ctx.state.set_data / ctx.state.set.) Default: change nothing.
        """
        return {}

    async def after_invoke(
        self, ctx: NodeContext, result: StateInterface
    ) -> "str | BaseMessage | None":
        """Shape the OUTPUT after a successful call — same contract as on_result.

        `result` is the model's output (read result.last_message / .last_message_content).
        RETURN the node's message: a str (→ AIMessage), a BaseMessage (as-is), or None
        (suppress). Write side data via ctx.state. Default: return the raw model message.
        """
        return result.last_message

    async def on_error(
        self, ctx: NodeContext, error: Exception
    ) -> "str | BaseMessage | None":
        """Handle a failure of the LLM call.

        Default: re-raise, so unhandled errors are never silently swallowed. Override to
        RETURN a fallback message (str | BaseMessage | None) and keep the graph alive. ctx
        carries the input (ctx.state) and this thread's history (ctx.history).
        """
        raise error
