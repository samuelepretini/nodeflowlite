"""DTO of a graph node: a reference to an agent.

The node configuration (model, prompt, tools) lives in the agent, not here:
the YAML is "thin" and only declares which agent occupies the node.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeDTO:
    name: str       # node name (key in the YAML)
    agent: str      # name of the referenced agent (resolved by the registry)
