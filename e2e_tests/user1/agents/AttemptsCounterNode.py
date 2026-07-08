"""Example node: a non-LLM node (level zero — direct NodeInterface).

This node needs no model and no tools, so it does NOT extend AbstractCommonNode:
it implements NodeInterface directly. Its invoke() is simply its own deterministic
logic, returning a partial state update — no LLM involved. This is the right base
whenever the work is pure Python (counters, validation, formatting, I/O via an
injected interface, ...).

Naming: suffix "Node" (not "Agent") to signal at a glance this is not an LLM agent.
In the YAML it is still referenced like any other node: `agent: AttemptsCounterNode`.
"""

from __future__ import annotations

from typing import Any, Mapping

from agent_platform.core.interface.NodeInterface import NodeInterface
from agent_platform.core.state.NodeContext import NodeContext


class AttemptsCounterNode(NodeInterface):
    async def invoke(self, ctx: NodeContext) -> Mapping[str, Any]:
        # Pure logic, no LLM: bump the attempts counter by one. (`ctx.history` is this
        # thread's read-only state history, available but unused here.)
        attempts = ctx.state.get("attempts", 0)
        return {"attempts": attempts + 1}
