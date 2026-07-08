"""Interface (persistence-internal): provides a ready Postgres connection pool.

This port lives INSIDE the persistence adapter, not in `core`: it references a
psycopg type (`AsyncConnectionPool`), and core must stay DB-free. It is the seam
between `db/` (owns the pool's life cycle) and the components that consume a pool —
the checkpointer today, the repositories tomorrow — so they can share one pool and
be tested against a fake.

`open()` returns an async context manager that opens the pool on enter and closes it
on exit. A consumer nests it inside its own `open()`.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable

from psycopg_pool import AsyncConnectionPool


@runtime_checkable
class ConnectionPoolProviderInterface(Protocol):
    def open(self) -> AbstractAsyncContextManager[AsyncConnectionPool]:
        """Open and manage the connection pool's life cycle; yield a ready pool."""
        ...
