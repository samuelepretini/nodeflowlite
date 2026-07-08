"""YamlGraphLoader: parses a graphs/*.yaml file into a GraphDTO.

It reads the "thin" YAML (topology only) and fills the typed graph model. No name is
resolved into a Python object here: types, reducers, agents and routers stay as
strings in the DTO — the registry resolves them later. Malformed input fails fast
with a message that points at the file and the offending section.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from ..DTO.ConditionalEdgeDTO import ConditionalEdgeDTO
from ..DTO.EdgeDTO import EdgeDTO
from ..DTO.GraphDTO import GraphDTO
from ..DTO.NodeDTO import NodeDTO
from ..DTO.SimpleEdgeDTO import SimpleEdgeDTO
from ..DTO.StateFieldDTO import StateFieldDTO
from ..interface.GraphLoaderInterface import GraphLoaderInterface


class YamlGraphLoader(GraphLoaderInterface):
    def load(self, path: Path) -> GraphDTO:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping):
            raise ValueError(f"{path}: top level must be a mapping, got {type(raw).__name__}")

        name = self._require(raw, "name", path)
        return GraphDTO(
            name=name,
            description=raw.get("description"),
            version=raw.get("version"),
            state=self._parse_state(raw.get("state") or {}, path),
            nodes=self._parse_nodes(raw.get("nodes") or {}, path),
            edges=self._parse_edges(raw.get("edges") or [], path),
        )

    def _parse_state(self, section: Mapping[str, Any], path: Path) -> tuple[StateFieldDTO, ...]:
        fields = []
        for field_name, spec in section.items():
            spec = spec or {}
            fields.append(
                StateFieldDTO(
                    name=field_name,
                    type=self._require(spec, "type", path, ctx=f"state.{field_name}"),
                    reducer=spec.get("reducer"),
                    optional=bool(spec.get("optional", False)),
                    has_default="default" in spec,
                    default=spec.get("default"),
                )
            )
        return tuple(fields)

    def _parse_nodes(self, section: Mapping[str, Any], path: Path) -> tuple[NodeDTO, ...]:
        nodes = []
        for node_name, spec in section.items():
            spec = spec or {}
            agent = self._require(spec, "agent", path, ctx=f"nodes.{node_name}")
            nodes.append(NodeDTO(name=node_name, agent=agent))
        return tuple(nodes)

    def _parse_edges(self, section: list[Mapping[str, Any]], path: Path) -> tuple[EdgeDTO, ...]:
        edges: list[EdgeDTO] = []
        for raw in section:
            source = self._require(raw, "from", path, ctx="edges")
            if "router" in raw:
                edges.append(
                    ConditionalEdgeDTO(
                        source=source,
                        router=raw["router"],
                        targets=tuple(raw.get("targets", ())),
                    )
                )
            else:
                target = self._require(raw, "to", path, ctx=f"edges (from: {source})")
                edges.append(SimpleEdgeDTO(source=source, target=target))
        return tuple(edges)

    @staticmethod
    def _require(spec: Mapping[str, Any], key: str, path: Path, ctx: str | None = None) -> Any:
        if key not in spec:
            where = f" in {ctx}" if ctx else ""
            raise ValueError(f"{path}: missing required key {key!r}{where}")
        return spec[key]
