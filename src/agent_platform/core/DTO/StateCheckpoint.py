"""DTO of a checkpoint: one lightweight row in a thread's history index.

It is the "menu row" the user picks from before asking for a full state: it carries
identity and position (which node wrote it, at which super-step, when), NOT the state
values themselves. To read the values, resolve it via `StateHistoryInterface.at(...)`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StateCheckpoint:
    checkpoint_id: str   # opaque id of the super-step's checkpoint
    node: str            # node that produced this checkpoint (the writer)
    step: int            # super-step index in the run
    created_at: str      # ISO-8601 timestamp of when the checkpoint was written
