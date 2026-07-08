"""Agent L3 — extracts structured data from the web text (LLM).

Input-shaping: build_prompt composes the prompt from execution_data (the current row
+ the web text). Output-shaping: on_result writes the model's answer back into
execution_data under `extracted`. No chat history, no messages channel.
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class AIExtractor(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"
    SYSTEM_PROMPT = (
        "Sei un estrattore di dati. Dal testo fornito, estrai il nome e l'indirizzo "
        "del dentista in modo conciso. Se l'indirizzo non c'è, rispondi 'KO'."
    )
    TOOLS = []

    def build_prompt(self, state: StateInterface) -> str:
        data = state.execution_data
        name = (data.get("current") or {}).get("name", "")
        web_text = data.get("web_text", "")
        return f"Nominativo: {name}\n\nTesto dal web:\n{web_text}\n\nEstrai nome e indirizzo."

    def on_result(self, ctx: NodeContext, result: StateInterface) -> None:
        answer = result.last_message.content if result.last_message else ""
        ctx.state.set_data("extracted", answer)
