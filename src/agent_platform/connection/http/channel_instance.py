"""FastAPI app factory.

`create_app` receives an already-activated `provider` (built and managed by the
PlatformManager) plus a configuration object, and exposes it over HTTP. The graph
subsystem is NOT activated here: the channel only serves a ready provider, which
keeps the HTTP layer decoupled from how graphs are built.
"""

from __future__ import annotations

from fastapi import FastAPI

from agent_platform.core.interface.GraphProviderInterface import GraphProviderInterface

from .channel_operativity.HttpSettings import HttpSettings
from .channel_status import health
from .routes import http_graphs_router


def create_app(
    *,
    provider: GraphProviderInterface,
    settings: HttpSettings | None = None,
) -> FastAPI:
    settings = settings or HttpSettings()

    app = FastAPI(title=settings.title)
    app.state.settings = settings
    app.state.graphs = provider  # ready provider, served as-is (no graph activation here)

    app.include_router(health.router)
    app.include_router(http_graphs_router.router)

    return app
