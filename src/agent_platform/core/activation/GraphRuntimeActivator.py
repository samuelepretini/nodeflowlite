"""GraphRuntimeActivator: activates and deactivates the graphs.

At startup it opens the `provider_factory` (which in turn opens resources such as
the Postgres checkpointer and builds the graphs) and keeps the provider ready; at
shutdown it closes everything.

It is FRAMEWORK-FREE: it knows nothing about HTTP/FastAPI. It is the adapter (e.g.
the connection/http lifespan) that decides WHEN to call start()/stop() and WHERE to
expose the obtained provider.
"""

from __future__ import annotations

from ..interface.GraphProviderFactoryInterface import GraphProviderFactoryInterface
from ..interface.GraphProviderInterface import GraphProviderInterface


class GraphRuntimeActivator:
    def __init__(self, factory: GraphProviderFactoryInterface) -> None:
        self._factory = factory
        self._cm = None
        self._provider: GraphProviderInterface | None = None

    async def start(self) -> GraphProviderInterface:
        """Opens the factory and returns the graph provider ready for use."""
        self._cm = self._factory.open()
        self._provider = await self._cm.__aenter__()
        return self._provider

    async def stop(self) -> None:
        """Closes the factory and releases the resources."""
        if self._cm is not None:
            await self._cm.__aexit__(None, None, None)
            self._cm = None
            self._provider = None
