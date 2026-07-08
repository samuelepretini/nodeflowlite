"""Builtin tool: current weather for a city (stub).

Implements ToolInterface. The model-facing argument schema (city: str) is derived
from the typed signature of invoke(). The result is hard-coded for now.
"""

from __future__ import annotations

from agent_platform.core.interface.ToolInterface import ToolInterface


class GetWeather(ToolInterface):
    name = "get_weather"
    description = "Return the current weather for a given city."

    async def invoke(self, city: str) -> str:
        return f"It is 18 degrees and clear sky in {city}."
