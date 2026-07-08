"""DTO of a field of the graph's shared state.

Immutable value object produced by the loader while reading the YAML. No logic:
it only describes *what* is written there (the type/reducer names stay strings; it
will be the registry that resolves them into Python objects).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StateFieldDTO:
    name: str                       # field name (key in the YAML)
    type: str                       # type name: str|int|float|bool|list|dict|<PythonClass>
    reducer: str | None = None      # reducer name (e.g. "add_messages"), optional
    optional: bool = False
    has_default: bool = False       # distinguishes "no default" from "default = None"
    default: Any = None
