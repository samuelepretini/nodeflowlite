"""Interface: a tool that an agent can call.

A tool is NOT a graph node: it is not in the topology, not connected by edges. It
is a capability that an agent node uses *inside* its invoke() (like
create_agent(model, tools=[...])). The agent declares its tools in the class and
binds them at construction; the model decides when to call them.

The argument schema the model needs is derived from the concrete, typed signature
of invoke() (like LangChain's @tool): e.g. invoke(self, a: int, b: int) -> int.

Design choices:
- name/description: what the model sees to decide whether and how to call the tool.
- invoke: the concrete implementation declares typed arguments; the builder derives
  the model-facing schema from that signature.
- Async, to allow tools that perform I/O.
- Framework-free domain contract; the builder adapts it to a LangChain tool.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ToolInterface(Protocol):
    name: str
    description: str

    async def invoke(self, **kwargs: Any) -> Any:
        """Execute the tool with the given (typed) arguments and return the result."""
        ...
