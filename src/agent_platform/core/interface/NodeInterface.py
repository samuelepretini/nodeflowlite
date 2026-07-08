"""Interface: a node of the graph.

A node is filled by an "agent". It receives the current shared state and returns a
PARTIAL state update (only the fields it changes); LangGraph merges that update
into the state, applying the reducers (e.g. add_messages).

Design choices:
- Input is the current state, read-only: the node reads the fields it needs by
  name (it does not know the state schema).
- Output is a PARTIAL update, not the whole state: returning the whole state would
  make reducers like add_messages double-append.
- No routing here: a node only updates the state; *where to go next* is decided by
  the edges/routers. (This differs from the original code where nodes used
  Command(goto=...).)
- Async, because nodes call models/tools. The node's configuration (model, prompt,
  tools) lives in the agent's constructor, not in this interface.

Framework-free: this is a domain contract. The builder wraps an implementation as a
LangGraph node, e.g. add_node("worker", agent.invoke).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..state.NodeContext import NodeContext


@runtime_checkable
class NodeInterface(Protocol):
    async def invoke(self, ctx: "NodeContext") -> Mapping[str, Any]:
        """Run on the per-call context (ctx); return a partial state update.

        `ctx` bundles everything the node needs, all bound to THIS call by the framework:
        - ctx.state   — the current graph state, read AND write (a WritableState): read
                        accessors plus ctx.state.set(field, value) / set_data(key, value);
        - ctx.history — read-only view of this thread's history (previous/at/checkpoints),
                        already bound to the thread_id — the node never sees a thread_id.
        The abstract bases construct `ctx` and hand it to the node's extension point; a
        node that implements this interface directly receives `ctx` as is, and may return
        a partial update (merged with whatever it staged on ctx.state).
        """
        ...
