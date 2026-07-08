"""Interface: the graph's shared state, as an OBJECT (not a bare mapping).

A node/router reads the running state through this facade instead of indexing a raw
dict: `state.messages`, `state.last_message_content`, `state.execution_data`, or
`state.get("x")` for a user-declared field. It is a read-only view over the state
LangGraph manages; WRITES go through the writable view nodes receive (WritableState),
collected into a partial update and merged by the reducers.

Framework-free domain contract. The builder wraps the dict LangGraph passes into a
concrete `State` before handing it to a node/router, so every level (L0–L3) and every
router sees a `StateInterface`, never a `Mapping`.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from langchain_core.messages import BaseMessage


@runtime_checkable
class StateInterface(Protocol):
    @property
    def messages(self) -> list[BaseMessage]:
        """The chat channel's messages (empty list if none)."""
        ...

    @property
    def last_message(self) -> BaseMessage | None:
        """The last message, or None if there is none."""
        ...

    @property
    def last_message_content(self) -> str:
        """The text content of the last message ("" if there is none, or non-text)."""
        ...

    @property
    def execution_data(self) -> dict[str, Any]:
        """The execution_data bag — the flow's runtime variables (a copy; {} if empty)."""
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """Read a user-declared state field by name (dict-style), with a default."""
        ...

    def as_dict(self) -> dict[str, Any]:
        """The underlying state as a plain dict (escape hatch / passthrough)."""
        ...
