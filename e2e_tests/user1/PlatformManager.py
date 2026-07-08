"""This project's PlatformManager: the single initiator of the deployment.

USER code. It declares only THIS project's info — which graphs/agents (the factory)
and which channel (the transport); the framework's AbstractPlatformManager owns the
startup/shutdown lifecycle (graphs up -> serve -> graphs down). The framework
(agent_platform) does not depend on this folder; only the reverse.

    uv run python e2e_tests/user1/PlatformManager.py        (needs OPENROUTER_API_KEY in .env)
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # this project's root: makes `agents`/`tools`/`routers` importable

from dotenv import load_dotenv

load_dotenv(HERE / ".env")  # this project's OpenRouter key (+ optional DATABASE_URI)

from agent_platform.connection.http.channel_operativity.HttpTransport import HttpTransport
from agent_platform.core.interface.CheckpointerProviderInterface import CheckpointerProviderInterface
from agent_platform.core.platform.AbstractPlatformManager import AbstractPlatformManager
from agent_platform.core.provider.YamlGraphProviderFactory import YamlGraphProviderFactory
from agent_platform.core.registry.StaticRegistry import StaticRegistry
from agent_platform.persistence.checkpoint.MemoryCheckpointerProvider import MemoryCheckpointerProvider
from agent_platform.persistence.checkpoint.PostgresCheckpointerProvider import PostgresCheckpointerProvider
from agent_platform.persistence.db.PostgresConnectionPoolProvider import PostgresConnectionPoolProvider

from agents.JudgeAgent import JudgeAgent
from agents.WorkerAgent import WorkerAgent
from routers.JudgeRouter import JudgeRouter

# ElaborateResidualDentists flow
from agents.SheetReader import SheetReader
from agents.LoopManager import LoopManager
from agents.TavilyExtract import TavilyExtract
from agents.AIExtractor import AIExtractor
from agents.AIFormatter import AIFormatter
from agents.SheetWriter import SheetWriter
from routers.RowExistenceRouter import RowExistenceRouter
from routers.LoopRouter import LoopRouter
from routers.ExtractionExistRouter import ExtractionExistRouter
from routers.AIResultCheckRouter import AIResultCheckRouter

logging.basicConfig(level=logging.INFO)


class PlatformManager(AbstractPlatformManager):
    def build_factory(self) -> YamlGraphProviderFactory:
        registry = StaticRegistry(
            agents={
                "WorkerAgent": WorkerAgent,
                "JudgeAgent": JudgeAgent,
                "SheetReader": SheetReader,
                "LoopManager": LoopManager,
                "TavilyExtract": TavilyExtract,
                "AIExtractor": AIExtractor,
                "AIFormatter": AIFormatter,
                "SheetWriter": SheetWriter,
            },
            routers={
                "JudgeRouter": JudgeRouter,
                "RowExistenceRouter": RowExistenceRouter,
                "LoopRouter": LoopRouter,
                "ExtractionExistRouter": ExtractionExistRouter,
                "AIResultCheckRouter": AIResultCheckRouter,
            },
        )
        return YamlGraphProviderFactory(
            graphs_dir=HERE / "graphs",
            registry=registry,
            checkpointer_provider=self._build_checkpointer_provider(),
        )

    def _build_checkpointer_provider(self) -> CheckpointerProviderInterface:
        # Composition root: it alone knows the concretes. Postgres if a DATABASE_URI
        # is configured, otherwise an in-memory checkpointer (handy for local runs).
        db_uri = os.environ.get("DATABASE_URI")
        if db_uri:
            return PostgresCheckpointerProvider(PostgresConnectionPoolProvider(db_uri))
        logging.getLogger(__name__).info("No DATABASE_URI set: using in-memory checkpointer.")
        return MemoryCheckpointerProvider()

    def build_transport(self) -> HttpTransport:
        return HttpTransport(port=8000)


if __name__ == "__main__":
    asyncio.run(PlatformManager().run())
