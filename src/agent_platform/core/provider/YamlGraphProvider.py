"""YamlGraphProvider: the real GraphProviderInterface, holding the built graphs.

It keeps the runtimes already built from the YAMLs (one per graph name) and resolves
them by name. It holds GraphRuntimeInterface values (never a concrete runtime): the
concrete LangGraphRuntime is created by the builder, not known here. Replaces the
development StaticGraphProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..interface.GraphProviderInterface import GraphProviderInterface
from ..interface.GraphRuntimeInterface import GraphRuntimeInterface


@dataclass
class YamlGraphProvider(GraphProviderInterface):
    runtimes: dict[str, GraphRuntimeInterface]
    # Graphs declared in YAML that failed to build: name -> reason. Kept so a lookup
    # of a known-but-unavailable graph yields a clear cause, not a bare "not found".
    failures: dict[str, str] = field(default_factory=dict)

    def get(self, name: str) -> GraphRuntimeInterface | None:
        return self.runtimes.get(name)

    def names(self) -> list[str]:
        return list(self.runtimes)

    def failure(self, name: str) -> str | None:
        return self.failures.get(name)
