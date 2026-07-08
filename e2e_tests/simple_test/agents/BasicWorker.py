"""Stub agent — level 1 (config-only, AbstractCommonNode).

The standard tool-calling agent, and the level you will use most. You declare ONLY
configuration; the framework owns everything else — converting tools, building the
model, the awaited LLM call, and producing the partial state update.

Set MODEL, SYSTEM_PROMPT and (optionally) TOOLS (a list of ToolInterface classes
from tools/). There is no method body to write at this level.
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode


class BasicWorker(AbstractCommonNode):
    MODEL = "openai/gpt-4o-mini"                 # TODO pick your model
    SYSTEM_PROMPT = "TODO: describe what this worker does."
    TOOLS = []                                    # TODO add tools, e.g. [Multiply]
