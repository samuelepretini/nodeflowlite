"""AbstractPlatformManager: brings up the whole platform, in order.

It is the single initiator of a deployment: it owns the startup/shutdown LIFECYCLE
(graph subsystem first, then the channel), so a concrete manager only declares its
own info — which graphs/agents (the factory) and which channel (the transport).

This is a Template Method, like AbstractCommonNode for nodes: the framework provides
run() (the technical lifecycle the user must not get wrong); the user's concrete
PlatformManager provides build_factory()/build_transport() (its composition).

Order = the green light: the transport (which starts accepting requests) is served
ONLY after the provider is ready. Framework-free: depends on the factory/transport
PORTS, never on Yaml or HTTP.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..activation.GraphRuntimeActivator import GraphRuntimeActivator
from ..interface.GraphProviderFactoryInterface import GraphProviderFactoryInterface
from ..interface.TransportInterface import TransportInterface


class AbstractPlatformManager(ABC):
    @abstractmethod
    def build_factory(self) -> GraphProviderFactoryInterface:
        """The factory that builds this deployment's graphs (e.g. from YAML)."""
        ...

    @abstractmethod
    def build_transport(self) -> TransportInterface:
        """The channel this deployment serves on (e.g. HTTP on a given port)."""
        ...

    async def run(self) -> None:
        """Start the graphs, serve the channel until shutdown, then stop the graphs."""
        transport = self.build_transport()
        activator = GraphRuntimeActivator(self.build_factory())
        provider = await activator.start()        # 1) graph subsystem up
        try:
            await transport.serve(provider)       # 2) channel up = green light, serves
        finally:
            await activator.stop()                # 3) graph subsystem down
