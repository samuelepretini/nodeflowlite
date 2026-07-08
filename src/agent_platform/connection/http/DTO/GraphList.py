"""HTTP DTO: list of available graphs (`/graphs` response)."""

from __future__ import annotations

from pydantic import BaseModel


class GraphList(BaseModel):
    graphs: list[str]
