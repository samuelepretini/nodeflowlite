"""AP-14 probe node (L0, no LLM).

Each iteration of the loop reads the thread's history FROM INSIDE the node — the
hard part of AP-14 (mid-run the engine is empty, so history reads the checkpointer)
— and records what it saw into the execution_data bag. Because the bag is returned
and merged, the evidence is visible from HTTP (/invoke?include_state or /state/at).

What we record per step:
- num_checkpoints: len(ctx.history.checkpoints()) — proves checkpoints() works in-node
  (it should GROW each iteration; if it stayed 0 the engine-only path would be broken).
- prev_count: ctx.previous.execution_data["count"] — proves ctx.previous (LOAD_PREVIOUS,
  no await) returns the real previous State in-node.
- back1_count / "ROOT": ctx.history.back(1) — proves back(n) walks the parent chain and
  raises CheckpointNotFoundError past the start.
"""

from __future__ import annotations

from typing import ClassVar

from agent_platform.core.abstract.AbstractNode import AbstractNode
from agent_platform.core.state.CheckpointNotFoundError import CheckpointNotFoundError
from agent_platform.core.state.NodeContext import NodeContext


class CounterProbe(AbstractNode):
    # Opt-in: get ctx.previous pre-resolved (no await), usable anywhere.
    LOAD_PREVIOUS: ClassVar[bool] = True

    async def run(self, ctx: NodeContext) -> None:
        count = ctx.state.execution_data.get("count", 0)

        # --- AP-14 in-node history (this is what we are verifying) ---
        prev = ctx.previous  # no await, tolerant at the root (empty State)
        checkpoints = await ctx.history.checkpoints()  # in-node → reads the checkpointer
        ctx.state.set_data(f"step{count}_num_checkpoints", len(checkpoints))
        ctx.state.set_data(f"step{count}_prev_count", prev.execution_data.get("count"))
        # back(0) = your input (latest committed), back(1) = one super-step earlier.
        # Recorded side by side so the "back(n) walks n steps" behaviour is visible.
        back0 = await ctx.history.back(0)
        ctx.state.set_data(f"step{count}_back0_count", back0.execution_data.get("count"))
        try:
            back1 = await ctx.history.back(1)
            ctx.state.set_data(f"step{count}_back1_count", back1.execution_data.get("count"))
        except CheckpointNotFoundError:
            ctx.state.set_data(f"step{count}_back1", "ROOT (no parent)")

        # advance the loop counter (lives in the auto-injected execution_data bag)
        ctx.state.set_data("count", count + 1)
