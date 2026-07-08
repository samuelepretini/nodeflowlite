"""PostgresConnectionPoolProvider: a psycopg AsyncConnectionPool behind the port.

It owns the pool's life cycle: on open() it creates the pool, opens it (via the
async context manager, the non-deprecated way — `open=False` in the constructor,
then `async with`), yields it, and closes it on exit.

The connection kwargs are the ones LangGraph's Postgres saver requires:
`autocommit=True` (the saver issues its own transactions) and `prepare_threshold=0`
(disable implicit prepared statements, which clash with pooled connections).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from psycopg_pool import AsyncConnectionPool

from .ConnectionPoolProviderInterface import ConnectionPoolProviderInterface

_CONNECTION_KWARGS: dict[str, Any] = {"autocommit": True, "prepare_threshold": 0}


class PostgresConnectionPoolProvider(ConnectionPoolProviderInterface):
    def __init__(self, db_uri: str, *, max_size: int = 20) -> None:
        self._db_uri = db_uri
        self._max_size = max_size

    @asynccontextmanager
    async def open(self) -> AsyncIterator[AsyncConnectionPool]:
        pool = AsyncConnectionPool(
            conninfo=self._db_uri,
            max_size=self._max_size,
            kwargs=_CONNECTION_KWARGS,
            open=False,  # open via the context manager below, not in the constructor
        )
        async with pool:
            yield pool
