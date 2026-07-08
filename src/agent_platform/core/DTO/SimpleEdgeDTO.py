"""DTO of a simple edge: source -> target (unconditional)."""

from __future__ import annotations

from dataclasses import dataclass

from .EdgeDTO import EdgeDTO


@dataclass(frozen=True)
class SimpleEdgeDTO(EdgeDTO):
    target: str     # destination node (or "END")
