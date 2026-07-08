"""Interface: snapshot of a thread's persisted state.

In practice compatible with LangGraph's `StateSnapshot`.

Convention: interfaces have the `Interface` suffix; the file has the same name
(CamelCase) as the class it contains.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class ThreadStateInterface(Protocol):
    values: Mapping[str, Any]
    next: tuple[str, ...]
