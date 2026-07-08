"""LangGraphStateHistory: the real StateHistoryInterface, backed by a compiled graph.

It is the adapter that isolates LangGraph's state-history reads behind the port. Bound
to one thread at construction, it translates our read-only navigation (previous / at /
checkpoints) into LangGraph reads, always SCOPED to the bound thread_id — a node can
never reach another thread.

Two LangGraph "doors", used deliberately:
- the CHECKPOINTER (`compiled.checkpointer`) is the storage: it returns committed
  checkpoints even while THIS thread is mid-run. We read the state VALUES through it
  (previous / at), so a node can recover a past state during its own execution. The
  compiled graph's own `aget_state*` is empty when queried re-entrantly from inside a
  running node, which is why we do NOT use it for the value getters.
- the COMPILED GRAPH (`aget_state_history`) yields tidy StateSnapshots that carry the
  node label (the parent's `next`). We use it for the `checkpoints()` index (an
  operator/HTTP browsing tool); when it comes back empty (the re-entrant, in-node case)
  we fall back to the checkpointer for the rows — without the node label, which only the
  engine knows.

LangGraph types never escape this module.
"""

from __future__ import annotations

from typing import Any

from ..DTO.StateCheckpoint import StateCheckpoint
from ..interface.StateHistoryInterface import StateHistoryInterface
from ..interface.StateInterface import StateInterface
from ..state.CheckpointNotFoundError import CheckpointNotFoundError
from ..state.State import State

# LangGraph's internal node names, shown as the topology sentinels in the index.
_INTERNAL_LABELS = {"__start__": "START", "__end__": "END"}


class LangGraphStateHistory(StateHistoryInterface):
    def __init__(self, compiled: Any, thread_id: str) -> None:
        self._compiled = compiled  # a compiled LangGraph graph
        self._thread_id = thread_id  # bound at construction; never a method arg

    async def previous(self) -> StateInterface:
        # The common case: one super-step back (== back(1)), forgiving at the root.
        try:
            return await self.back(1)
        except CheckpointNotFoundError:
            return State({})

    async def back(self, steps: int) -> StateInterface:
        # Walk the parent chain `steps` times via the checkpointer (works even mid-run,
        # from inside a running node; scoped to the bound thread). steps=0 = latest.
        #saver è l'oggetto Checkpointer
        saver = self._compiled.checkpointer
        snapshot = await saver.aget_tuple(self._config())
        for _ in range(steps):
            parent_config = snapshot.parent_config if snapshot is not None else None
            if not parent_config:
                raise CheckpointNotFoundError(f"back({steps})")  # not that many steps back
            snapshot = await saver.aget_tuple(parent_config)
        if snapshot is None:
            raise CheckpointNotFoundError(f"back({steps})")
        return State(self._values(snapshot))

    async def at(self, checkpoint_id: str) -> StateInterface:
        saver = self._compiled.checkpointer
        snapshot = await saver.aget_tuple(self._config(checkpoint_id))
        if snapshot is None:
            raise CheckpointNotFoundError(checkpoint_id)  # thread-scoped: never a leak
        return State(self._values(snapshot))

    async def checkpoints(self, limit: int | None = None) -> list[StateCheckpoint]:
        rows = await self._checkpoints_via_graph(limit)
        if rows:
            return rows  # external/post-run: tidy snapshots WITH node labels
        return await self._checkpoints_via_saver(limit)  # in-node fallback (no node label)

    async def _checkpoints_via_graph(self, limit: int | None) -> list[StateCheckpoint]:
        # The node that PRODUCED a checkpoint is the one its PARENT (the previous
        # super-step) was about to run — i.e. the parent's `next`. So we keep a one-step
        # lookahead over the older-adjacent snapshot.
        snapshots: list[Any] = []
        async for snapshot in self._compiled.aget_state_history(self._config()):
            snapshots.append(snapshot)
            if limit is not None and len(snapshots) > limit:
                break  # one extra, so the last emitted row can read its parent's `next`
        rows: list[StateCheckpoint] = []
        for index, snapshot in enumerate(snapshots):
            if limit is not None and len(rows) >= limit:
                break
            parent = snapshots[index + 1] if index + 1 < len(snapshots) else None
            producers = parent.next if parent is not None else ()  # node(s) that wrote this step
            node = ", ".join(_INTERNAL_LABELS.get(name, name) for name in producers)  # __start__ -> START
            rows.append(
                StateCheckpoint(
                    checkpoint_id=(snapshot.config.get("configurable") or {}).get("checkpoint_id", ""),
                    node=node,  # CHOICE: join when a step ran parallel nodes
                    step=(snapshot.metadata or {}).get("step", -1),
                    created_at=snapshot.created_at or "",
                )
            )
        return rows

    async def _checkpoints_via_saver(self, limit: int | None) -> list[StateCheckpoint]:
        # Re-entrant (in-node) fallback: the engine's history is empty mid-run, so read
        # the rows straight from storage. The node label is left empty — only the engine
        # knows it (via `next`), and it isn't carried on the raw checkpoint.
        saver = self._compiled.checkpointer
        rows: list[StateCheckpoint] = []
        async for tuple_ in saver.alist(self._config()):
            if limit is not None and len(rows) >= limit:
                break
            checkpoint = tuple_.checkpoint
            configurable = tuple_.config.get("configurable", {})
            rows.append(
                StateCheckpoint(
                    checkpoint_id=configurable.get("checkpoint_id", "") or checkpoint.get("id", ""),
                    node="",  # EXAMPLE: not derivable from the raw checkpoint (no `next`)
                    step=(tuple_.metadata or {}).get("step", -1),
                    created_at=checkpoint.get("ts", ""),
                )
            )
        return rows

    @staticmethod
    def _values(tuple_: Any) -> dict[str, Any]:
        # The checkpointer returns RAW channels: the user-facing state fields PLUS
        # LangGraph internals (routing channels like 'branch:to:x', the '__start__' input
        # wrapper). Keep only the user channels — drop namespaced (':') and dunder ('__')
        # ones — so the recovered State looks like the one the nodes see.
        channels = tuple_.checkpoint.get("channel_values", {})
        return {key: value for key, value in channels.items() if ":" not in key and not key.startswith("__")}

    def _config(self, checkpoint_id: str | None = None) -> dict[str, Any]:
        configurable: dict[str, Any] = {"thread_id": self._thread_id}
        if checkpoint_id is not None:
            configurable["checkpoint_id"] = checkpoint_id
        return {"configurable": configurable}
