"""CheckpointNotFoundError: raised when a checkpoint_id is not found on the thread.

Domain error (framework-free). `StateHistoryInterface.at(checkpoint_id)` raises it when
the bound thread has no checkpoint with that id; an adapter maps it to its transport
error (the HTTP layer turns it into a 404). It is SCOPED to the bound thread, so an id
that belongs to another thread is simply "not found" here — never a cross-thread leak.
"""

from __future__ import annotations


class CheckpointNotFoundError(Exception):
    def __init__(self, checkpoint_id: str) -> None:
        super().__init__(f"no checkpoint {checkpoint_id!r} on this thread")
        self.checkpoint_id = checkpoint_id
