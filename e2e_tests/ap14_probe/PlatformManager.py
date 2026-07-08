"""AP-14 probe deployment — the single initiator of this test server.

A minimal, LLM-FREE deployment to exercise AP-14 by hand:
- in-memory checkpointer (no DATABASE_URI, no Postgres),
- one L0 node + one router (no OPENROUTER_API_KEY needed),
- HTTP on :8000.

    uv run python PlatformManager.py        (no .env required)

Then drive it with ./ap14_curls.sh (see README.md).
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # makes this project's `agents`/`routers` importable

from agent_platform.connection.http.channel_operativity.HttpTransport import HttpTransport
from agent_platform.core.platform.AbstractPlatformManager import AbstractPlatformManager
from agent_platform.core.provider.YamlGraphProviderFactory import YamlGraphProviderFactory
from agent_platform.core.registry.StaticRegistry import StaticRegistry
from agent_platform.persistence.checkpoint.MemoryCheckpointerProvider import MemoryCheckpointerProvider

from agents.CounterProbe import CounterProbe
from routers.LoopRouter import LoopRouter

logging.basicConfig(level=logging.INFO)


class PlatformManager(AbstractPlatformManager):
    def build_factory(self) -> YamlGraphProviderFactory:
        registry = StaticRegistry(
            agents={"CounterProbe": CounterProbe},
            routers={"LoopRouter": LoopRouter},
        )
        return YamlGraphProviderFactory(
            graphs_dir=HERE / "graphs",
            registry=registry,
            checkpointer_provider=MemoryCheckpointerProvider(),
        )

    def build_transport(self) -> HttpTransport:
        # Override with PORT=... if 8000 is busy (e.g. another graph server running).
        return HttpTransport(port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    asyncio.run(PlatformManager().run())
