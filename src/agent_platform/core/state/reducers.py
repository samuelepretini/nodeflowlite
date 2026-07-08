"""Built-in state reducers owned by the framework (the channel-merge functions).

A reducer decides how a node's PARTIAL update is merged into a state channel. The
chat channel uses LangGraph's `add_messages`; this module holds the framework's own
reducers (referenced by name in the registry / auto-injected by the builder).
"""

from __future__ import annotations

from typing import Any, Mapping


def merge_dicts(current: Mapping[str, Any] | None, update: Mapping[str, Any] | None) -> dict[str, Any]:
    """Shallow-merge a dict update onto the current value (keys in `update` win).

    Handles the initial `None` (first write to the channel). Used for the
    `execution_data` bag: a node returns `{"execution_data": {k: v}}` and it is
    merged in, not replaced. (Removing a key is not expressible via a plain merge.)
    """
    return {**(current or {}), **(update or {})}
