"""Interface: read-only access to a thread's state history.

Bound to a single thread at construction (the `thread_id` is NOT a method argument):
the caller obtains one of these from `GraphRuntimeInterface.history(thread_id)` and then
navigates the run's super-steps — read the previous state, jump to a specific checkpoint,
or list the lightweight index of checkpoints. Strictly read-only: rollback/resume is a
separate concern (AP-13) and lives elsewhere.

Framework-free domain contract. Adapting from the real LangGraph state history
(`aget_state` / `aget_state_history`, mapping snapshots to `State`/`StateCheckpoint`) is
the responsibility of the adapter in `core/runtime`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..DTO.StateCheckpoint import StateCheckpoint
    from .StateInterface import StateInterface


@runtime_checkable
class StateHistoryInterface(Protocol):
    async def previous(self) -> StateInterface:
        """The state of the PREVIOUS super-step (the one before the latest). == back(1),
        but forgiving: returns an empty state at the root instead of raising."""
        ...

    async def back(self, steps: int) -> StateInterface:
        """The state `steps` super-steps back from the latest committed checkpoint.

        steps=0 is the latest (in-node: your own input); steps=1 is the previous; etc.
        Raises CheckpointNotFoundError if the thread has fewer than `steps` of history.
        """
        ...

    async def at(self, checkpoint_id: str) -> StateInterface:
        """The state captured at the given checkpoint.

        Raises CheckpointNotFoundError if the bound thread has no such checkpoint
        (thread-scoped — an id from another thread is "not found", never exposed).
        """
        ...

    async def checkpoints(self, limit: int | None = None) -> list[StateCheckpoint]:
        """The lightweight checkpoint index, newest-first (optionally capped)."""
        ...
