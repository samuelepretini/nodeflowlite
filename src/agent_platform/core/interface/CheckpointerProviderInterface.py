"""Interface: provides the checkpointer that persists a graph's thread state.

A checkpointer is what LangGraph uses to save/restore each thread's state (so
`thread_id` resumes a conversation and `get_state` can read it back). WHERE that
state lives — in memory, in Postgres, ... — is a persistence concern that must stay
out of `core` (Ports & Adapters: no DB imports in core). This port hides it.

`open()` manages the checkpointer's LIFE CYCLE: it returns an async context manager
that, on enter, sets up the resource (e.g. a Postgres connection pool + tables) and
yields a ready `BaseCheckpointSaver`; on exit it tears the resource down. The graph
provider factory nests this inside its own `open()`, so the connection lives exactly
as long as the served graphs.

`BaseCheckpointSaver` is a LangGraph type — and LangGraph is the engine the platform
is built on (batteries included), not an external system to isolate — so naming it
here does not break the framework-free rule. The DB-specific code (psycopg, the
Postgres saver) lives in the `persistence` adapter, never in core.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable

from langgraph.checkpoint.base import BaseCheckpointSaver


@runtime_checkable
class CheckpointerProviderInterface(Protocol):
    def open(self) -> AbstractAsyncContextManager[BaseCheckpointSaver]:
        """Open and manage the checkpointer's life cycle; yield a ready saver."""
        ...
