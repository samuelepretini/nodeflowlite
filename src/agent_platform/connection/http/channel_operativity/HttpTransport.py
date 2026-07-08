"""HttpTransport: serves a ready provider over HTTP (FastAPI + uvicorn).

The HTTP adapter of TransportInterface. It receives an already-activated provider,
builds the FastAPI app around it (`create_app`) and runs the uvicorn server until
shutdown. It does NOT activate the graph subsystem — that already happened before
serve() is called (the PlatformManager guarantees the order).
"""

from __future__ import annotations

import uvicorn

from agent_platform.core.interface.GraphProviderInterface import GraphProviderInterface
from agent_platform.core.interface.TransportInterface import TransportInterface

from ..channel_instance import create_app
from .HttpSettings import HttpSettings


class HttpTransport(TransportInterface):
    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8000,
        settings: HttpSettings | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._settings = settings

    async def serve(self, provider: GraphProviderInterface) -> None:
        app = create_app(provider=provider, settings=self._settings)
        config = uvicorn.Config(app, host=self._host, port=self._port)
        await uvicorn.Server(config).serve()
