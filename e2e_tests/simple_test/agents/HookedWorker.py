"""Stub agent — level 2 (lifecycle hooks, AbstractHookedNode).

Same configuration as a level-1 worker, but you gain three hooks AROUND the LLM
call, each with a safe default (so override only the ones you need):
- before_invoke: validate/transform the INPUT; return ONLY the changed fields.
- after_invoke:  shape the OUTPUT; RETURN the node's message (str | BaseMessage |
  None). Default: the raw model message.
- on_error:      fallback to keep the graph alive; default re-raises.

The sealed invoke() orchestrates: before -> LLM core -> after, guarded by on_error.
You never touch async plumbing beyond returning from these hooks.
"""

from __future__ import annotations

from typing import Any, Mapping

from langchain_core.messages import BaseMessage

from agent_platform.core.abstract.AbstractHookedNode import AbstractHookedNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class HookedWorker(AbstractHookedNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: describe what this worker does."
    TOOLS = []                                    # TODO add tools

    async def before_invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # TODO transform/validate the input. Return ONLY changed fields ({} = no change).
        return {}

    async def after_invoke(
        self, ctx: NodeContext, result: StateInterface
    ) -> "str | BaseMessage | None":
        # TODO shape the output: RETURN the node's message (str | BaseMessage | None).
        # Default: return the raw model message.
        return result.last_message

    async def on_error(
        self, ctx: NodeContext, error: Exception
    ) -> "str | BaseMessage | None":
        # TODO return a fallback message to survive the error. Default: re-raise.
        return await super().on_error(ctx, error)
