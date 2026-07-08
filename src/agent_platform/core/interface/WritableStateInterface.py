"""Interface: the running state a NODE works on — read AND write.

A node receives this (as `ctx.state`) instead of the read-only StateInterface: it
extends the read facade with the writes a node needs, so the node reads and writes
through ONE object. Routers and the AP-14 history keep the read-only StateInterface
(they must not write), so the write methods exist only where they make sense.

Writes do NOT mutate the snapshot you read: they are STAGED and the framework collects
them into the node's partial update, which the reducers merge into the NEXT super-step
(execution_data via the merge reducer, declared fields by overwrite). So reading a key
back in the SAME call still returns the input value — the change flows forward, it does
not edit the snapshot in place.

The node's OUTPUT MESSAGE is NOT set here: it is the return value of the agent's
`on_result` (str | BaseMessage | None), owned by the framework — see AbstractCommonNode.
"""

from __future__ import annotations

from typing import Any

from .StateInterface import StateInterface


class WritableStateInterface(StateInterface):
    def set(self, field: str, value: Any) -> None:
        """Write a declared state field (overwrite semantics). Staged, not in-place."""
        ...

    def set_data(self, key: str, value: Any) -> None:
        """Add/overwrite one entry in the execution_data bag (merge semantics). Staged."""
        ...
