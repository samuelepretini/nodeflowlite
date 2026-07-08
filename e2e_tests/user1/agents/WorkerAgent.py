"""Example agent: a worker that answers using the available tools.

It only declares configuration; all the machinery (tool conversion, model,
invoke) is inherited from AbstractCommonNode.
"""

from __future__ import annotations

from agent_platform.core.abstract.AbstractCommonNode import AbstractCommonNode

from tools.GetWeather import GetWeather
from tools.Multiply import Multiply


class WorkerAgent(AbstractCommonNode):
    MODEL = "openai/gpt-4o"
    SYSTEM_PROMPT = "You are an assistant that answers using the available tools. Answer concisely."
    TOOLS = [Multiply, GetWeather]
