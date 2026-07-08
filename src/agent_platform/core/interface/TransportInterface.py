"""Interface: a long-running transport that serves graphs over a channel.

It receives a READY provider and serves it (HTTP, CLI, gRPC, ...) until shutdown.
It is a driven port: the PlatformManager starts it after the graphs are up, so the
channel never has to activate the graph subsystem — it only serves it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .GraphProviderInterface import GraphProviderInterface


@runtime_checkable
class TransportInterface(Protocol):
    async def serve(self, provider: GraphProviderInterface) -> None:
        """Serve the (already ready) provider until shutdown."""
        ...
