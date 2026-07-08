"""MemoryCheckpointerProvider: an in-memory checkpointer (no database).

The dev/test strategy of CheckpointerProviderInterface: it yields a LangGraph
`MemorySaver`, so threads and `get_state` work without Postgres. State lives only
for the process lifetime — fine for local runs and tests, not for production.

It is the composition root's choice (e.g. when no DATABASE_URI is set) between this
and PostgresCheckpointerProvider; the rest of the system depends only on the port.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver

from agent_platform.core.interface.CheckpointerProviderInterface import (
    CheckpointerProviderInterface,
)


class MemoryCheckpointerProvider(CheckpointerProviderInterface):
    @asynccontextmanager
    async def open(self) -> AsyncIterator[BaseCheckpointSaver]:
        # Nothing to set up or tear down: an in-memory saver has no external resource.
        yield MemorySaver()
