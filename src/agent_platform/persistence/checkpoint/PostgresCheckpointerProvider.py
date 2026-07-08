"""PostgresCheckpointerProvider: persists thread state in Postgres.

The production strategy of CheckpointerProviderInterface. It does NOT own the
connection itself: it receives a ConnectionPoolProviderInterface (IoC) and builds
the LangGraph `AsyncPostgresSaver` on top of the pool that collaborator yields. So
`db/` owns the pool, `checkpoint/` owns the saver — and the same pool can later be
shared with repositories.

`open()` nests the pool's life cycle inside its own: open the pool, build the saver,
`setup()` it (creates the checkpoint tables if missing), yield it, and let the pool
close on exit.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agent_platform.core.interface.CheckpointerProviderInterface import (
    CheckpointerProviderInterface,
)

from ..db.ConnectionPoolProviderInterface import ConnectionPoolProviderInterface


class PostgresCheckpointerProvider(CheckpointerProviderInterface):
    def __init__(self, pool_provider: ConnectionPoolProviderInterface) -> None:
        self._pool_provider = pool_provider

    @asynccontextmanager
    async def open(self) -> AsyncIterator[BaseCheckpointSaver]:
        async with self._pool_provider.open() as pool:
            saver = AsyncPostgresSaver(pool)
            await saver.setup()  # idempotent: creates the checkpoint tables if missing
            yield saver
