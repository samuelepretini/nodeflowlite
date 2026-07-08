"""Builtin tool: multiply two integers.

Implements ToolInterface. The model-facing argument schema (a: int, b: int) is
derived from the typed signature of invoke().
"""

from __future__ import annotations

from agent_platform.core.interface.ToolInterface import ToolInterface


class Multiply(ToolInterface):
    name = "multiply"
    description = "Multiply two integers and return the product."

    async def invoke(self, a: int, b: int) -> int:
        return a * b
