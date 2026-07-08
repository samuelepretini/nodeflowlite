"""Stub agent — a judge that validates the worker and drives a quality loop.

A level-3 agent (AbstractCommonNode + on_result): the LLM produces a judgment, then
on_result writes the fields the router reads — `verdict` ("OK" / "KO...") and an
incremented `attempts` (via ctx.state.set). On a KO it RETURNs its critique as a
HumanMessage so the worker sees it on the next loop.

Pair it with a router (QualityRouter) on a conditional edge:
    judge -> router -> worker (retry) | END (done)
The judge EVALUATES one answer; the router OWNS the stop policy (max attempts).
Keep those two responsibilities split.
"""

from __future__ import annotations

from typing import Any, Mapping

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode
from agent_platform.core.interface.StateInterface import StateInterface
from agent_platform.core.state.NodeContext import NodeContext


class JudgeAgent(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: reply 'OK' if the answer is complete, else 'KO' + a short critique."
    TOOLS = []

    def on_result(self, ctx: NodeContext, result: StateInterface):
        # TODO read the judgment (result.last_message_content) and set the verdict.
        # Stub: always approve so the loop terminates. Write fields via ctx.state.set;
        # RETURN None to emit no message (the final reply stays the worker's answer).
        attempts = ctx.state.get("attempts", 0) + 1
        ctx.state.set("attempts", attempts)
        ctx.state.set("verdict", "OK")
        return None
