"""
HTTP layer configuration.

Minimal for now: once the `config` package exists, it will build and
populate this object (from env/file). The HTTP layer receives it ready to use.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HttpSettings(BaseModel):
    title: str = "Agent Platform"
    api_token: str | None = Field(
        default=None,
        description="Bearer token to protect the endpoints. If None, auth is disabled.",
    )
