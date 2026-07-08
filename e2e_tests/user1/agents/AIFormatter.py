"""Agent L3 — formats the address into a normalised form (LLM).

Input-shaping: build_prompt composes the prompt from the extracted data in
execution_data. Output-shaping: on_result writes the formatted address back into
execution_data under `formatted_address`. No chat history, no messages channel.
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class AIFormatter(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"
    SYSTEM_PROMPT = (
        "Formatta l'indirizzo nel formato: via e numero civico, CAP, città. "
        "Rispondi solo con l'indirizzo formattato, niente altro."
    )
    TOOLS = []

    def build_prompt(self, state: StateInterface) -> str:
        extracted = state.execution_data.get("extracted", "")
        return f"Dati estratti:\n{extracted}\n\nRestituisci l'indirizzo formattato."

    def on_result(self, ctx: NodeContext, result: StateInterface) -> None:
        formatted = result.last_message.content if result.last_message else ""
        ctx.state.set_data("formatted_address", formatted)
