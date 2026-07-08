"""Example agent: a judge that validates the worker's answer and drives the loop.

It is the second half of the quality loop (worker -> judge -> back to worker | END).
The routing decision lives in JudgeRouter; this agent's job is to EVALUATE and write
the state the router reads: it produces `{verdict, attempts}` on top of the usual
message channel.

Level 3 (custom output): it extends AbstractCommonNode and overrides the SYNCHRONOUS
`on_result`. The base owns the LLM call and the await; this agent only shapes the
output — no async, no `self._agent`, no raw `messages` channel (it uses the helpers):
- it reads the judge model's verdict from the last produced message (OK / KO ...),
- it bumps `attempts` (there is no separate counter node in this graph),
- on OK it leaves `messages` untouched, so the graph's final reply stays the WORKER's
  answer (not the word "OK"),
- on KO it appends the critique as a HumanMessage, so the worker sees it on the next
  loop and improves — exactly the feedback the loop needs.

The "max attempts" decision is NOT here: it is a routing concern and lives in
JudgeRouter. This agent always emits a plain OK/KO verdict.
"""

from __future__ import annotations

from typing import Any, ClassVar, Mapping

from langchain_core.messages import HumanMessage

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode

from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.interface.ToolInterface import ToolInterface
from agent_platform.core.state.NodeContext import NodeContext


class JudgeAgent(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"  # a lighter model is enough to judge
    SYSTEM_PROMPT = (
        "You are a strict judge. Evaluate the worker's latest answer against the "
        "user's original request. Reply with 'OK' (and nothing else) if the answer "
        "fully provides every piece of information that was requested; otherwise "
        "reply with 'KO' followed by a short note of what is missing or wrong. The "
        "available tools (weather, multiplication) are reliable: trust their results."
    )
    TOOLS: ClassVar[list[type[ToolInterface]]] = []  # the judge reasons, it does not act

    def on_result(
        self, ctx: NodeContext, result: StateInterface
    ) -> "HumanMessage | None":
        # Synchronous: the base already awaited the judge model; we just shape output.
        verdict_text = result.last_message_content.strip()
        attempts = ctx.state.get("attempts", 0) + 1
        ctx.state.set("attempts", attempts)

        if verdict_text.startswith("OK"):
            # No message: the final reply must stay the worker's answer.
            ctx.state.set("verdict", "OK")
            return None

        # KO: feed the critique back as a HumanMessage so the worker sees it on the next
        # loop. The model's text already starts with "KO ...", so don't re-prefix it.
        ctx.state.set("verdict", "KO")
        return HumanMessage(content=verdict_text)
