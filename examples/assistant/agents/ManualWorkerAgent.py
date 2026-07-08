"""Example agent: a worker that shapes its own output (level 3).

It extends AbstractCommonNode and overrides the SYNCHRONOUS hook on_result: the
base owns the LLM call and the await, then hands the resolved result here. on_result
RETURNS the node's message (str | BaseMessage | None) and the framework emits it — no
self._agent, no raw "messages" channel, nothing to remember to return.

This example adds a small custom rule (a fallback when the model produced no
message). For full control over the orchestration itself (multiple model calls,
branching, retries), override invoke() instead and call `await self.ai_invoke(state)`.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext

from tools.GetWeather import GetWeather
from tools.Multiply import Multiply


class ManualWorkerAgent(AbstractCommonNode):
    MODEL = "openai/gpt-4o"
    SYSTEM_PROMPT = "You are an assistant that answers using the available tools. Answer concisely."
    TOOLS = [Multiply, GetWeather]

    def on_result(self, ctx: NodeContext, result: StateInterface) -> "BaseMessage":
        # Synchronous: no await, no self._agent. Custom rule: guard an empty result.
        message = result.last_message
        if message is None:
            return AIMessage(content="No answer produced.")
        return message
