"""Example agent: a worker with lifecycle hooks (level 2).

Same configuration as WorkerAgent, but it extends AbstractHookedNode to gain
control around the LLM call. It overrides all three hooks to show their typical
use:
- before_invoke: observe / validate / transform the input before the LLM runs,
- after_invoke: post-process the result (here it may also modify the output),
- on_error: return a fallback message instead of letting the exception crash the
  graph.

The point of this level: override only the hooks you need, the rest stays
inherited from the base (defaults: no-op / pass-through / re-raise).
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from langchain_core.messages import AIMessage, BaseMessage

from agent_platform.core.abstract.AbstractHookedNode import AbstractHookedNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext

from tools.GetWeather import GetWeather
from tools.Multiply import Multiply

logger = logging.getLogger(__name__)


class ResilientWorkerAgent(AbstractHookedNode):
    MODEL = "openai/gpt-4o"
    SYSTEM_PROMPT = "You are an assistant that answers using the available tools. Answer concisely."
    TOOLS = [Multiply, GetWeather]

    async def before_invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # Example: observability + a sanity check that MODIFIES the input — here we
        # trim whitespace from the incoming messages before the LLM sees them.
        # We return ONLY the changed field; the framework preserves the rest.
        messages = ctx.state.messages
        if not messages:
            logger.warning("ResilientWorkerAgent: invoked with no messages")
        logger.info("ResilientWorkerAgent: starting with %d message(s)", len(messages))
        cleaned = [
            m.model_copy(update={"content": m.content.strip()})
            if isinstance(m, BaseMessage) and isinstance(m.content, str)
            else m
            for m in messages
        ]
        return {"messages": cleaned}  # input partial: what the model will see

    async def after_invoke(
        self, ctx: NodeContext, result: StateInterface
    ) -> "BaseMessage | None":
        # Example: shape the OUTPUT — trim trailing whitespace from the produced message.
        # RETURN the node's message (str | BaseMessage | None).
        message = result.last_message
        logger.info("ResilientWorkerAgent: produced %s", "a message" if message else "nothing")
        if isinstance(message, AIMessage) and isinstance(message.content, str):
            return message.model_copy(update={"content": message.content.rstrip()})
        return message

    async def on_error(
        self, ctx: NodeContext, error: Exception
    ) -> "BaseMessage | None":
        # Keep the graph alive: surface the failure as a normal message instead
        # of propagating the exception.
        return AIMessage(content=f"Sorry, the request failed: {error}")
