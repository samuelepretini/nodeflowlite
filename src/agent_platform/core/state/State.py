"""State: the real StateInterface — an object facade over the running state mapping.

It wraps the dict LangGraph passes to a node/router and exposes typed accessors, so
agents read `state.messages` / `state.last_message_content` / `state.execution_data` /
`state.get(...)` instead of indexing a raw dict. Read-only: writes go through the
writable view (WritableState) and are merged by the reducers — never through this object.
"""

from __future__ import annotations

from typing import Any, Mapping

from langchain_core.messages import BaseMessage

from ..interface.StateInterface import StateInterface


class State(StateInterface):
    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data: dict[str, Any] = dict(data)

    @property
    def messages(self) -> list[BaseMessage]:
        return list(self._data.get("messages", []))

    @property
    def last_message(self) -> BaseMessage | None:
        messages = self.messages
        return messages[-1] if messages else None

    @property
    def last_message_content(self) -> str:
        last = self.last_message
        content = last.content if last else ""
        return content if isinstance(content, str) else ""

    @property
    def execution_data(self) -> dict[str, Any]:
        return dict(self._data.get("execution_data") or {})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)
