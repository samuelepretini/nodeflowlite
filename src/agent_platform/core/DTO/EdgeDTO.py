"""Base of a graph edge.

There are two concrete variants (one file each): SimpleEdgeDTO and
ConditionalEdgeDTO. The base holds only what they have in common: the starting
node.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeDTO:
    source: str     # starting node (or "START")
