"""Stub agent — level 3 (shape input/output, AbstractCommonNode).

The framework owns the LLM call and all the message plumbing. It offers two SIMPLE
SYNCHRONOUS hooks (strings/updates only — no list juggling):
- build_prompt(state): shape the INPUT — get the prompt, modify it with runtime
  variables, return it. TRANSIENT: it changes only what the model sees, the persisted
  history stays raw. (For a PERSISTED input change, use a HookedWorker's before_invoke.)
- on_result(state, result, ctx): shape the OUTPUT — build the node's partial update.

Override either or both. For full control of the message list override build_messages;
for full control of the orchestration override invoke() and call ai_invoke(state).
"""

from __future__ import annotations

from typing import Any, Mapping

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class ShapingWorker(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: describe what this worker does."
    TOOLS = []                                    # TODO add tools

    def build_prompt(self, state: StateInterface) -> str:
        text = state.last_message_content                    # get
        # EXAMPLE: 'customer' is a sample execution_data key — use your own variables.
        customer = state.execution_data.get("customer", "")  # a runtime variable
        return f"{text}\n\nCustomer: {customer}"             # modify + return

    def on_result(self, ctx: NodeContext, result: StateInterface):
        # Shape the OUTPUT: RETURN the node's message — a str, a BaseMessage, or None
        # (suppress). Write side data via ctx.state.set_data / ctx.state.set; reach this
        # thread's history via ctx.history. Default: return the raw model message.
        return result.last_message
