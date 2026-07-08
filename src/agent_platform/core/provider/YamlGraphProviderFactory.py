"""YamlGraphProviderFactory: builds the provider from a folder of graphs/*.yaml.

It is the assembly point of the graph-building subsystem: on open() it wires the
loader + registry + builder and produces a runtime per YAML, then yields a ready
provider. Its constructor holds the configuration (graphs folder + the injected
checkpointer provider). Replaces the development DevGraphProviderFactory.

The checkpointer is NOT created here: it is injected as a CheckpointerProviderInterface
(IoC), so this factory stays free of any DB import (Ports & Adapters). The composition
root picks the concrete strategy — in-memory for dev/tests, Postgres for production —
and this factory just nests its life cycle inside its own open(): the connection lives
exactly as long as the served graphs. A single graph that fails to build is skipped
with a warning, so one broken YAML never takes down the whole server.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from ..builder.GraphBuilder import GraphBuilder
from ..interface.CheckpointerProviderInterface import CheckpointerProviderInterface
from ..interface.GraphLoaderInterface import GraphLoaderInterface
from ..interface.GraphProviderFactoryInterface import GraphProviderFactoryInterface
from ..interface.RegistryInterface import RegistryInterface
from ..loader.YamlGraphLoader import YamlGraphLoader
from .YamlGraphProvider import YamlGraphProvider

logger = logging.getLogger(__name__)


class YamlGraphProviderFactory(GraphProviderFactoryInterface):
    def __init__(
        self,
        *,
        graphs_dir: Path | str,
        registry: RegistryInterface,
        checkpointer_provider: CheckpointerProviderInterface,
        loader: GraphLoaderInterface | None = None,
    ) -> None:
        self._graphs_dir = Path(graphs_dir)
        self._registry = registry
        self._checkpointer_provider = checkpointer_provider
        self._loader = loader or YamlGraphLoader()

    @asynccontextmanager
    async def open(self):
        async with self._checkpointer_provider.open() as checkpointer:
            builder = GraphBuilder(self._registry, checkpointer)

            runtimes = {}
            failures: dict[str, str] = {}
            for path in sorted(self._graphs_dir.glob("*.yaml")):
                name = path.stem  # best-known id until the YAML is loaded
                try:
                    graph = self._loader.load(path)
                    name = graph.name
                    runtimes[name] = builder.build(graph)
                    logger.info("Built graph %r from %s", name, path.name)
                except Exception as error:
                    failures[name] = str(error)
                    logger.warning("Skipping graph %s: %s", path.name, error)

            if failures:
                # Loud, aggregated summary so a skipped graph is never missed in the
                # startup noise — the provider also keeps the reasons (see failure()).
                summary = "; ".join(f"{name} ({reason})" for name, reason in failures.items())
                logger.error(
                    "%d graph(s) FAILED to build and are NOT being served: %s",
                    len(failures),
                    summary,
                )

            yield YamlGraphProvider(runtimes, failures)
