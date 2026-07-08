"""WritableState: the read+write state object a node works on (ctx.state).

It reuses State's read accessors and adds the node's writes. Writes are STAGED into a
separate buffer (never mutating the input snapshot) and exposed to the framework via
`collect()`, which the builder turns into the node's partial update. So:
- reads (`messages`, `last_message_content`, `execution_data`, `get`) see the INPUT;
- `set`/`set_data` stage the OUTPUT, merged by the reducers into the NEXT super-step.

Per-call object (built by GraphBuilder._as_node), never stored on the shared node
instance — concurrency-safe by construction.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..interface.WritableStateInterface import WritableStateInterface
from .State import State

EXECUTION_DATA_FIELD = "execution_data"


class WritableState(State, WritableStateInterface):
    def __init__(self, data: Mapping[str, Any]) -> None:
        super().__init__(data)
        self._staged: dict[str, Any] = {}

    def set(self, field: str, value: Any) -> None:
        # Stage a declared-field write (overwrite). Not visible to reads in this call.
        self._staged[field] = value

    def set_data(self, key: str, value: Any) -> None:
        # Stage one execution_data entry; the merge reducer integrates it downstream.
        bag = self._staged.setdefault(EXECUTION_DATA_FIELD, {})
        bag[key] = value

    def collect(self) -> dict[str, Any]:
        """The staged partial update (copied; {} when nothing was written)."""
        update = dict(self._staged)
        if EXECUTION_DATA_FIELD in update:
            update[EXECUTION_DATA_FIELD] = dict(update[EXECUTION_DATA_FIELD])
        return update

    def with_input(self, extra: Mapping[str, Any]) -> "WritableState":
        """A new view with `extra` merged onto the READ input, SHARING the staged buffer.

        Used by L2 before_invoke to feed transformed input to the LLM call without
        losing any output already staged.
        """
        merged = WritableState({**self._data, **extra})
        merged._staged = self._staged  # share: writes land in the same buffer
        return merged
